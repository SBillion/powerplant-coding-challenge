import logging
from app.models import PowerPlant, FuelPrices, PowerPlantWithCostAndPower
from app.schemas import ProductionResponseItem

logger = logging.getLogger(__name__)


class ProductionPlanService:
    """
    Service class to handle production plan calculations.
    """

    # CO2 emissions per MWh for gas-fired plants
    CO2_EMISSIONS_PER_MWH = 0.3

    # Power output precision (0.1 MW)
    POWER_PRECISION = 0.1

    @staticmethod
    async def calculate_cost_per_mwh(
        powerplant: PowerPlant, fuels: FuelPrices
    ) -> float:
        """
        Calculate cost per MWh for a powerplant.

        - Wind turbines: Free (cost = 0)
        - Gas-fired: Gas cost + CO2 emissions cost, adjusted for efficiency
        - Turbojet: Kerosine cost, adjusted for efficiency

        Args:
            powerplant: The powerplant to calculate cost for
            fuels: Current fuel prices

        Returns:
            Cost per MWh
        """
        if powerplant.type == "windturbine":
            return 0.0

        elif powerplant.type == "gasfired":
            gas_cost = fuels.gas / powerplant.efficiency
            co2_cost = (
                fuels.co2 * ProductionPlanService.CO2_EMISSIONS_PER_MWH
            ) / powerplant.efficiency
            return gas_cost + co2_cost

        elif powerplant.type == "turbojet":
            return fuels.kerosine / powerplant.efficiency

    @staticmethod
    async def _round_power(value: float) -> float:
        """Round power value to 0.1 MW precision."""
        precision = ProductionPlanService.POWER_PRECISION
        return round(value / precision) * precision

    @staticmethod
    def _is_negligible(value: float) -> bool:
        """Check if a value is negligible (below precision threshold)."""
        return abs(value) <= ProductionPlanService.POWER_PRECISION

    @staticmethod
    def _can_allocate_to_plant(desired_power: float, plant_min: float) -> bool:
        """Check if desired power meets plant's minimum requirement."""
        return desired_power >= plant_min

    @staticmethod
    def _apply_allocations(
        powerplants: list[PowerPlantWithCostAndPower], allocations: list[float]
    ) -> None:
        """Apply allocation values to powerplants."""
        for i, powerplant in enumerate(powerplants):
            powerplant.allocated_power = allocations[i]

    @staticmethod
    async def _try_greedy_allocation(
        powerplants: list[PowerPlantWithCostAndPower], load: float
    ) -> tuple[list[float], float]:
        """
        Phase 1: Try greedy allocation, respecting minimum power constraints.

        Returns:
            Tuple of (allocations list, total allocated power)
        """
        n = len(powerplants)
        allocations = [0.0] * n
        remaining = load

        for i in range(n):
            if ProductionPlanService._is_negligible(remaining):
                break

            desired = min(powerplants[i].pmax, remaining)

            if ProductionPlanService._can_allocate_to_plant(
                desired, powerplants[i].pmin
            ):
                allocated = await ProductionPlanService._round_power(desired)
                allocations[i] = allocated
                remaining -= allocated

        return allocations, sum(allocations)

    @staticmethod
    def _try_activate_plant_at_minimum(
        powerplants: list[PowerPlantWithCostAndPower],
        allocations: list[float],
        reamining: float,
    ) -> tuple[list[float], float]:
        """
        Phase 2a: Try activating unallocated plants at their minimum power.

        Returns:
            Tuple of (updated allocations, remaining shortfall)
        """
        n = len(powerplants)

        for i in range(n):
            if allocations[i] > 0:
                continue  # Already allocated

            plant_min = powerplants[i].pmin
            if plant_min <= reamining + ProductionPlanService.POWER_PRECISION:
                allocations[i] = plant_min
                reamining -= plant_min

                if ProductionPlanService._is_negligible(reamining):
                    break

        return allocations, reamining

    @staticmethod
    def _reduce_allocation_to_make_room(
        powerplants: list[PowerPlantWithCostAndPower],
        allocations: list[float],
        up_to_index: int,
        room_needed: float,
    ) -> float:
        """
        Reduce earlier allocations (down to their minimum) to free up capacity.

        Returns:
            Amount of room actually created
        """
        room_created = 0.0

        for j in range(up_to_index):
            if allocations[j] == 0:
                continue

            can_reduce = allocations[j] - powerplants[j].pmin
            if can_reduce > 0:
                reduction = min(can_reduce, room_needed - room_created)
                allocations[j] -= reduction
                room_created += reduction

                if room_created >= room_needed:
                    break

        return room_created

    @staticmethod
    def _try_backtracking_allocation(
        powerplants: list[PowerPlantWithCostAndPower],
        allocations: list[float],
        shortfall: float,
    ) -> tuple[list[float], float]:
        """
        Phase 2b: Try activating expensive plants by reducing cheaper ones.

        Returns:
            Tuple of (updated allocations, remaining shortfall)
        """
        n = len(powerplants)

        for i in range(n):
            if allocations[i] > 0 or ProductionPlanService._is_negligible(shortfall):
                continue

            plant_min = powerplants[i].pmin
            if plant_min <= 0:
                continue

            # Calculate how much room we need to create
            room_needed = plant_min - shortfall

            if room_needed > 0:
                room_created = ProductionPlanService._reduce_allocation_to_make_room(
                    powerplants, allocations, i, room_needed
                )
                shortfall += room_created

            # Try to activate this plant
            if plant_min <= shortfall + ProductionPlanService.POWER_PRECISION:
                allocations[i] = plant_min
                shortfall -= plant_min

                if ProductionPlanService._is_negligible(shortfall):
                    break

        return allocations, shortfall

    @staticmethod
    async def _allocate_power(
        powerplants: list[PowerPlantWithCostAndPower], load: float
    ) -> list[PowerPlantWithCostAndPower]:
        """
        Allocate power to powerplants to meet the required load.

        Uses a three-phase algorithm:
        1. Greedy allocation: Assign power to cheapest plants first
        2. Handle shortfall: Activate plants at minimum or backtrack to make room

        Args:
            powerplants: Sorted list of powerplants by cost (cheapest first)
            load: Required power load in MW

        Returns:
            List of powerplants with allocated power

        Raises:
            ValueError: If load cannot be met with available capacity
        """
        # Handle zero/negligible load
        if ProductionPlanService._is_negligible(load):
            ProductionPlanService._apply_allocations(
                powerplants, [0.0] * len(powerplants)
            )
            return powerplants

        # Phase 1: Greedy allocation
        allocations, total = await ProductionPlanService._try_greedy_allocation(
            powerplants, load
        )

        # Check if we're done
        if ProductionPlanService._is_negligible(total - load):
            # Apply rounding to final allocations
            for i in range(len(allocations)):
                allocations[i] = await ProductionPlanService._round_power(
                    allocations[i]
                )
            ProductionPlanService._apply_allocations(powerplants, allocations)
            return powerplants

        # Phase 2: Handle remaining (we allocated less than needed)
        if total < load - ProductionPlanService.POWER_PRECISION:
            remaining = load - total

            # Phase 2a: Try activating plants at minimum
            allocations, remaining = (
                ProductionPlanService._try_activate_plant_at_minimum(
                    powerplants, allocations, remaining
                )
            )

            # Phase 2b: If still short, try backtracking
            if remaining > ProductionPlanService.POWER_PRECISION:
                allocations, remaining = (
                    ProductionPlanService._try_backtracking_allocation(
                        powerplants, allocations, remaining
                    )
                )

        # Final validation
        total = sum(allocations)
        if ProductionPlanService._is_negligible(total - load):
            # Apply rounding to final allocations
            for i in range(len(allocations)):
                allocations[i] = await ProductionPlanService._round_power(
                    allocations[i]
                )
            ProductionPlanService._apply_allocations(powerplants, allocations)
            return powerplants

        # Failed to meet load
        capacity = sum(p.pmax for p in powerplants)
        min_total = sum(p.pmin for p in powerplants if p.pmin > 0)

        logger.error(
            f"Unable to meet load {load}MW. Allocated: {total}MW. "
            f"Available capacity: {capacity}MW, Minimum required: {min_total}MW"
        )
        raise ValueError("Unable to meet the required load with available powerplants.")

    @staticmethod
    async def _prepare_powerplants_in_merit_order(
        powerplants: list[PowerPlant], fuels: FuelPrices
    ) -> list[PowerPlantWithCostAndPower]:
        """
        Sort powerplants by cost (merit order) and adjust capacities.

        Wind turbines have their capacity adjusted based on wind percentage.
        Plants are sorted by cost per MWh (cheapest first), then by capacity.

        Args:
            powerplants: List of available powerplants
            fuels: Current fuel prices and wind percentage

        Returns:
            List of powerplants with costs, sorted by merit order
        """
        plants_with_cost = []

        for plant in powerplants:
            cost = await ProductionPlanService.calculate_cost_per_mwh(plant, fuels)

            plant_with_cost = PowerPlantWithCostAndPower(
                **plant.model_dump(),
                cost_per_mwh=cost,
            )

            # Adjust wind turbine capacity based on wind availability
            if plant.type == "windturbine":
                plant_with_cost.pmax = plant.pmax * (fuels.wind / 100)
                plant_with_cost.pmin = 0
            else:
                plant_with_cost.pmin = min(plant.pmin, plant.pmax)

            plants_with_cost.append(plant_with_cost)

        # Sort by cost (cheapest first), then by capacity (largest first)
        plants_with_cost.sort(key=lambda x: (x.cost_per_mwh, -x.pmax))
        return plants_with_cost

    @staticmethod
    async def _create_response(
        allocated_plants: list[PowerPlantWithCostAndPower],
    ) -> list[ProductionResponseItem]:
        """
        Create response items from allocated powerplants.

        Args:
            allocated_plants: List of powerplants with allocated power

        Returns:
            List of response items with plant name and power output
        """
        return [
            ProductionResponseItem(name=plant.name, p=plant.allocated_power)
            for plant in allocated_plants
        ]

    @staticmethod
    async def calculate_production_plan(
        load: float, fuels: FuelPrices, powerplants: list[PowerPlant]
    ) -> list[ProductionResponseItem]:
        """
        Calculate optimal production plan using merit-order algorithm.

        Steps:
        1. Calculate cost per MWh for each powerplant
        2. Adjust wind turbine capacity based on wind percentage
        3. Sort powerplants by cost (cheapest first)
        4. Allocate power to meet load, respecting min/max constraints
        5. Return power output for each plant

        Args:
            load: Required power load in MW
            fuels: Current fuel prices and wind percentage
            powerplants: Available powerplants

        Returns:
            List of power outputs for each plant

        Raises:
            ValueError: If load cannot be met
        """
        logger.info("Calculating production plan for load: %s MW", load)

        # Sort powerplants by cost (merit order)
        ordered_plants = (
            await ProductionPlanService._prepare_powerplants_in_merit_order(
                powerplants, fuels
            )
        )

        # Allocate power to meet the load
        allocated_plants = await ProductionPlanService._allocate_power(
            ordered_plants, load
        )

        logger.info("Production plan calculation completed.")
        return await ProductionPlanService._create_response(allocated_plants)
