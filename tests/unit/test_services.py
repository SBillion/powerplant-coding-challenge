import pytest
from app.services import ProductionPlanService
from app.models import PowerPlant, FuelPrices, PowerPlantWithCostAndPower
from tests.unit.conftest import COST_CALCULATION_PARAMS


class TestCalculateCostPerMwh:
    """Tests for calculate_cost_per_mwh method."""

    @pytest.mark.parametrize(
        "plant_name,plant_type,efficiency,pmin,pmax,gas,kerosine,co2,wind,expected_cost,description",
        COST_CALCULATION_PARAMS,
    )
    @pytest.mark.asyncio
    async def test_cost_calculation(
        self,
        plant_name,
        plant_type,
        efficiency,
        pmin,
        pmax,
        gas,
        kerosine,
        co2,
        wind,
        expected_cost,
        description,
    ):
        """Test cost calculation for different powerplant types."""
        powerplant = PowerPlant(
            name=plant_name,
            type=plant_type,
            efficiency=efficiency,
            pmin=pmin,
            pmax=pmax,
        )
        fuels = FuelPrices(
            **{
                "gas(euro/MWh)": gas,
                "kerosine(euro/MWh)": kerosine,
                "co2(euro/ton)": co2,
                "wind(%)": wind,
            }
        )

        cost = await ProductionPlanService.calculate_cost_per_mwh(powerplant, fuels)

        assert cost == expected_cost, description


class TestAllocatePower:
    """Tests for _allocate_power method."""

    @pytest.mark.asyncio
    async def test_allocate_single_plant_exact_match(self):
        """Single powerplant with exact capacity should be fully allocated."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=0,
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=0,
            )
        ]

        result = await ProductionPlanService._allocate_power(plants, 100.0)

        assert len(result) == 1
        assert result[0].allocated_power == 100.0

    @pytest.mark.asyncio
    async def test_allocate_below_pmin_sets_to_zero(self):
        """Allocation below pmin should be set to zero."""
        plants = [
            PowerPlantWithCostAndPower(
                name="plant1",
                type="gasfired",
                efficiency=0.5,
                pmin=50,
                pmax=100,
                cost_per_mwh=20.0,
                allocated_power=0,
            )
        ]

        with pytest.raises(ValueError, match="Unable to meet the required load"):
            await ProductionPlanService._allocate_power(plants, 30.0)

    @pytest.mark.asyncio
    async def test_allocate_multiple_plants(
        self, plant_with_cost_wind, plant_with_cost_gas
    ):
        """Multiple plants should be allocated in order."""
        plants = [plant_with_cost_wind, plant_with_cost_gas]

        result = await ProductionPlanService._allocate_power(plants, 120.0)

        assert len(result) == 2
        assert result[0].allocated_power == 50.0
        assert result[1].allocated_power == 70.0


class TestPreparePowerplantsInMeritOrder:
    """Tests for _prepare_powerplants_in_merit_order method."""

    @pytest.mark.asyncio
    async def test_sorts_by_cost(self, gas_fired_plant, sample_fuels):
        """Plants should be sorted by cost per MWh."""
        wind_plant = PowerPlant(
            name="wind1", type="windturbine", efficiency=1.0, pmin=0, pmax=50
        )
        plants = [gas_fired_plant, wind_plant]
        fuels = sample_fuels

        result = await ProductionPlanService._prepare_powerplants_in_merit_order(
            plants, fuels
        )

        assert result[0].name == "wind1"  # Lower cost
        assert result[1].name == "gas1"

    @pytest.mark.asyncio
    async def test_adjusts_wind_capacity(self, wind_turbine):
        """Wind turbine capacity should be adjusted by wind percentage."""
        plants = [wind_turbine]
        fuels = FuelPrices(
            **{
                "gas(euro/MWh)": 10.0,
                "kerosine(euro/MWh)": 20.0,
                "co2(euro/ton)": 20.0,
                "wind(%)": 60.0,
            }
        )

        result = await ProductionPlanService._prepare_powerplants_in_merit_order(
            plants, fuels
        )

        assert result[0].pmax == 60.0
        assert result[0].pmin == 0


class TestCreateResponse:
    """Tests for _create_response method."""

    @pytest.mark.asyncio
    async def test_creates_response_items(self, allocated_plants):
        """Should create ProductionResponseItem for each powerplant."""
        plants = allocated_plants

        result = await ProductionPlanService._create_response(plants)

        assert len(result) == 2
        assert result[0].name == "plant1"
        assert result[0].p == 50.0
