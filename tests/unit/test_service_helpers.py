"""
Tests for ProductionPlanService helper methods.
These tests cover the internal allocation algorithm methods.
"""

import pytest
from app.services import ProductionPlanService
from app.models import PowerPlantWithCostAndPower


class TestCanAllocateToPlant:
    """Tests for _can_allocate_to_plant helper method."""

    def test_desired_power_exceeds_minimum(self):
        """Should return True when desired power exceeds minimum."""
        result = ProductionPlanService._can_allocate_to_plant(
            desired_power=100.0, plant_min=50.0
        )
        assert result is True

    def test_desired_power_equals_minimum(self):
        """Should return True when desired power equals minimum."""
        result = ProductionPlanService._can_allocate_to_plant(
            desired_power=50.0, plant_min=50.0
        )
        assert result is True

    def test_desired_power_below_minimum(self):
        """Should return False when desired power is below minimum."""
        result = ProductionPlanService._can_allocate_to_plant(
            desired_power=30.0, plant_min=50.0
        )
        assert result is False

    def test_zero_minimum(self):
        """Should return True for any desired power when minimum is zero."""
        result = ProductionPlanService._can_allocate_to_plant(
            desired_power=10.0, plant_min=0.0
        )
        assert result is True


class TestApplyAllocations:
    """Tests for _apply_allocations helper method."""

    def test_applies_allocations_to_plants(self):
        """Should apply allocation values to powerplants."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=0,
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=0,
            ),
            PowerPlantWithCostAndPower(
                name="plant2",
                type="windturbine",
                efficiency=1.0,
                pmin=0,
                pmax=50,
                cost_per_mwh=0.0,
                allocated_power=0,
            ),
        ]
        allocations = [75.0, 25.0]

        ProductionPlanService._apply_allocations(plants, allocations)

        assert plants[0].allocated_power == 75.0
        assert plants[1].allocated_power == 25.0

    def test_applies_zero_allocations(self):
        """Should apply zero allocations correctly."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=10,
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=50.0,  # Previously allocated
            ),
        ]
        allocations = [0.0]

        ProductionPlanService._apply_allocations(plants, allocations)

        assert plants[0].allocated_power == 0.0


class TestTryGreedyAllocation:
    """Tests for _try_greedy_allocation method."""

    @pytest.mark.asyncio
    async def test_allocates_to_single_plant(self):
        """Should allocate full load to single plant if it can handle it."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=0,
                pmax=200,
                cost_per_mwh=20.0,
                allocated_power=0,
            ),
        ]

        allocations, total = await ProductionPlanService._try_greedy_allocation(
            plants, 100.0
        )

        assert len(allocations) == 1
        assert allocations[0] == 100.0
        assert total == 100.0

    @pytest.mark.asyncio
    async def test_allocates_across_multiple_plants(self):
        """Should allocate across multiple plants in order."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="windturbine",
                efficiency=1.0,
                pmin=0,
                pmax=50,
                cost_per_mwh=0.0,
                allocated_power=0,
            ),
            PowerPlantWithCostAndPower(
                name="plant2",
                type="gasfired",
                efficiency=0.5,
                pmin=0,
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=0,
            ),
        ]

        allocations, total = await ProductionPlanService._try_greedy_allocation(
            plants, 120.0
        )

        assert allocations[0] == 50.0  # Wind fully allocated
        assert allocations[1] == 70.0  # Gas partially allocated
        assert total == 120.0

    @pytest.mark.asyncio
    async def test_skips_plant_below_pmin(self):
        """Should skip plant if desired allocation is below pmin."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=50,  # Minimum is 50
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=0,
            ),
        ]

        allocations, total = await ProductionPlanService._try_greedy_allocation(
            plants,
            30.0,  # Only need 30, less than pmin
        )

        assert allocations[0] == 0.0
        assert total == 0.0

    @pytest.mark.asyncio
    async def test_rounds_allocation_correctly(self):
        """Should round allocations to precision."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=0,
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=0,
            ),
        ]

        allocations, total = await ProductionPlanService._try_greedy_allocation(
            plants, 33.33
        )

        assert abs(allocations[0] - 33.3) < 0.01  # Rounded to 0.1
        assert abs(total - 33.3) < 0.01


class TestTryActivatePlantAtMinimum:
    """Tests for _try_activate_plant_at_minimum method."""

    def test_activates_plant_at_minimum(self):
        """Should activate plant at minimum when shortfall permits."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=40,
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=0,
            ),
        ]
        allocations = [0.0]
        shortfall = 50.0

        new_allocations, new_shortfall = (
            ProductionPlanService._try_activate_plant_at_minimum(
                plants, allocations, shortfall
            )
        )

        assert new_allocations[0] == 40.0
        assert new_shortfall == 10.0

    def test_skips_already_allocated_plants(self):
        """Should skip plants that already have allocation."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=30,
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=50.0,
            ),
            PowerPlantWithCostAndPower(
                name="plant2",
                type="turbojet",
                efficiency=0.4,
                pmin=20,
                pmax=50,
                cost_per_mwh=50.0,
                allocated_power=0,
            ),
        ]
        allocations = [50.0, 0.0]
        shortfall = 25.0

        new_allocations, new_shortfall = (
            ProductionPlanService._try_activate_plant_at_minimum(
                plants, allocations, shortfall
            )
        )

        assert new_allocations[0] == 50.0  # Unchanged
        assert new_allocations[1] == 20.0  # Activated at pmin
        assert new_shortfall == 5.0

    def test_stops_when_shortfall_is_met(self):
        """Should stop activating plants once shortfall is negligible."""
        plants = [
            PowerPlantWithCostAndPower(
                name=f"plant{i}",
                type="gasfired",
                efficiency=0.5,
                pmin=20,
                pmax=50,
                cost_per_mwh=20.0 + i,
                allocated_power=0,
            )
            for i in range(3)
        ]
        allocations = [0.0, 0.0, 0.0]
        shortfall = 20.0

        new_allocations, new_shortfall = (
            ProductionPlanService._try_activate_plant_at_minimum(
                plants, allocations, shortfall
            )
        )

        assert new_allocations[0] == 20.0
        assert new_allocations[1] == 0.0  # Should not activate
        assert new_allocations[2] == 0.0
        assert abs(new_shortfall) <= ProductionPlanService.POWER_PRECISION


class TestReduceAllocationToMakeRoom:
    """Tests for _reduce_allocation_to_make_room method."""

    def test_reduces_single_allocation(self):
        """Should reduce a single allocation to create room."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=20,
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=80.0,
            ),
        ]
        allocations = [80.0]
        room_needed = 30.0

        room_created = ProductionPlanService._reduce_allocation_to_make_room(
            plants, allocations, up_to_index=1, room_needed=room_needed
        )

        assert room_created == 30.0
        assert allocations[0] == 50.0  # 80 - 30

    def test_reduces_multiple_allocations(self):
        """Should reduce multiple allocations to create needed room."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=20,
                pmax=100,
                cost_per_mwh=10.0,
                allocated_power=50.0,
            ),
            PowerPlantWithCostAndPower(
                name="plant2",
                type="gasfired",
                efficiency=0.5,
                pmin=30,
                pmax=100,
                cost_per_mwh=15.0,
                allocated_power=60.0,
            ),
        ]
        allocations = [50.0, 60.0]
        room_needed = 50.0

        room_created = ProductionPlanService._reduce_allocation_to_make_room(
            plants, allocations, up_to_index=2, room_needed=room_needed
        )

        assert room_created == 50.0
        assert allocations[0] == 20.0  # Reduced by 30 (down to pmin)
        assert allocations[1] == 40.0  # Reduced by 20

    def test_respects_plant_minimum(self):
        """Should not reduce allocation below plant minimum."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=40,
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=50.0,
            ),
        ]
        allocations = [50.0]
        room_needed = 20.0

        room_created = ProductionPlanService._reduce_allocation_to_make_room(
            plants, allocations, up_to_index=1, room_needed=room_needed
        )

        assert room_created == 10.0  # Can only reduce by 10 (50 - 40)
        assert allocations[0] == 40.0  # Stopped at pmin

    def test_skips_zero_allocations(self):
        """Should skip plants with zero allocation."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=20,
                pmax=100,
                cost_per_mwh=10.0,
                allocated_power=0.0,
            ),
            PowerPlantWithCostAndPower(
                name="plant2",
                type="gasfired",
                efficiency=0.5,
                pmin=30,
                pmax=100,
                cost_per_mwh=15.0,
                allocated_power=60.0,
            ),
        ]
        allocations = [0.0, 60.0]
        room_needed = 20.0

        room_created = ProductionPlanService._reduce_allocation_to_make_room(
            plants, allocations, up_to_index=2, room_needed=room_needed
        )

        assert room_created == 20.0
        assert allocations[0] == 0.0  # Unchanged
        assert allocations[1] == 40.0


class TestTryBacktrackingAllocation:
    """Tests for _try_backtracking_allocation method."""

    def test_activates_expensive_plant_by_reducing_cheap_plant(self):
        """Should activate expensive plant by reducing cheaper one."""
        plants = [
            PowerPlantWithCostAndPower(
                name="cheap",
                type="gasfired",
                efficiency=0.5,
                pmin=20,
                pmax=100,
                cost_per_mwh=10.0,
                allocated_power=80.0,
            ),
            PowerPlantWithCostAndPower(
                name="expensive",
                type="turbojet",
                efficiency=0.4,
                pmin=50,
                pmax=80,
                cost_per_mwh=50.0,
                allocated_power=0,
            ),
        ]
        allocations = [80.0, 0.0]
        shortfall = 20.0  # Need 20 more, but plant needs 50 minimum

        new_allocations, new_shortfall = (
            ProductionPlanService._try_backtracking_allocation(
                plants, allocations, shortfall
            )
        )

        assert new_allocations[0] == 50.0  # Reduced by 30 to make room
        assert new_allocations[1] == 50.0  # Activated at pmin
        assert abs(new_shortfall) <= ProductionPlanService.POWER_PRECISION

    def test_skips_already_allocated_plants(self):
        """Should skip plants that are already allocated."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=30,
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=50.0,
            ),
        ]
        allocations = [50.0]
        shortfall = 10.0

        new_allocations, new_shortfall = (
            ProductionPlanService._try_backtracking_allocation(
                plants, allocations, shortfall
            )
        )

        assert new_allocations[0] == 50.0  # Unchanged
        assert new_shortfall == 10.0  # Unchanged

    def test_skips_zero_pmin_plants(self):
        """Should skip plants with zero pmin."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="windturbine",
                efficiency=1.0,
                pmin=0,
                pmax=50,
                cost_per_mwh=0.0,
                allocated_power=0,
            ),
        ]
        allocations = [0.0]
        shortfall = 10.0

        new_allocations, new_shortfall = (
            ProductionPlanService._try_backtracking_allocation(
                plants, allocations, shortfall
            )
        )

        assert new_allocations[0] == 0.0
        assert new_shortfall == 10.0

    def test_stops_when_shortfall_negligible(self):
        """Should stop when shortfall becomes negligible."""
        plants = [
            PowerPlantWithCostAndPower(
                name=f"plant{i}",
                type="gasfired",
                efficiency=0.5,
                pmin=30,
                pmax=100,
                cost_per_mwh=20.0 + i * 10,
                allocated_power=0,
            )
            for i in range(3)
        ]
        allocations = [0.0, 0.0, 0.0]
        shortfall = 30.0

        new_allocations, new_shortfall = (
            ProductionPlanService._try_backtracking_allocation(
                plants, allocations, shortfall
            )
        )

        assert new_allocations[0] == 30.0
        assert new_allocations[1] == 0.0  # Should not try to activate
        assert new_allocations[2] == 0.0
        assert abs(new_shortfall) <= ProductionPlanService.POWER_PRECISION


class TestIsNegligible:
    """Tests for _is_negligible helper method."""

    def test_returns_true_for_zero(self):
        """Should return True for zero value."""
        result = ProductionPlanService._is_negligible(0.0)
        assert result is True

    def test_returns_true_for_value_below_precision(self):
        """Should return True for values below precision threshold."""
        result = ProductionPlanService._is_negligible(0.05)
        assert result is True

    def test_returns_true_for_negative_value_below_precision(self):
        """Should return True for negative values below precision threshold."""
        result = ProductionPlanService._is_negligible(-0.08)
        assert result is True

    def test_returns_false_for_value_above_precision(self):
        """Should return False for values above precision threshold."""
        result = ProductionPlanService._is_negligible(0.2)
        assert result is False

    def test_returns_true_for_exact_precision(self):
        """Should return True for value equal to precision."""
        result = ProductionPlanService._is_negligible(
            ProductionPlanService.POWER_PRECISION
        )
        assert result is True
