"""Fixtures for unit tests."""

import pytest
from app.models import PowerPlant, FuelPrices, PowerPlantWithCostAndPower


# Import shared fixtures and data from parent conftest
from tests.conftest import PAYLOAD1, PAYLOAD2, PAYLOAD3, RESPONSE3


@pytest.fixture
def sample_fuels():
    """Sample fuel prices for testing."""
    return FuelPrices(
        **{
            "gas(euro/MWh)": 10.0,
            "kerosine(euro/MWh)": 20.0,
            "co2(euro/ton)": 20.0,
            "wind(%)": 50.0,
        }
    )


@pytest.fixture
def wind_turbine():
    """Sample wind turbine powerplant."""
    return PowerPlant(
        name="wind1", type="windturbine", efficiency=1.0, pmin=0, pmax=100
    )


@pytest.fixture
def gas_fired_plant():
    """Sample gas-fired powerplant."""
    return PowerPlant(name="gas1", type="gasfired", efficiency=0.5, pmin=10, pmax=100)


@pytest.fixture
def turbojet_plant():
    """Sample turbojet powerplant."""
    return PowerPlant(name="jet1", type="turbojet", efficiency=0.4, pmin=5, pmax=50)


@pytest.fixture
def plant_with_cost_wind():
    """Sample wind turbine with cost and allocated power."""
    return PowerPlantWithCostAndPower(
        name="plant1",
        type="windturbine",
        efficiency=1.0,
        pmin=0,
        pmax=50,
        cost_per_mwh=0.0,
        allocated_power=0,
    )


@pytest.fixture
def plant_with_cost_gas():
    """Sample gas-fired powerplant with cost and allocated power."""
    return PowerPlantWithCostAndPower(
        name="plant2",
        type="gasfired",
        efficiency=0.5,
        pmin=0,
        pmax=100,
        cost_per_mwh=20.0,
        allocated_power=0,
    )


@pytest.fixture
def allocated_plants():
    """Sample list of allocated powerplants."""
    return [
        PowerPlantWithCostAndPower(
            name="plant1",
            type="gasfired",
            efficiency=0.5,
            pmin=10,
            pmax=100,
            cost_per_mwh=20.0,
            allocated_power=50.0,
        ),
        PowerPlantWithCostAndPower(
            name="plant2",
            type="windturbine",
            efficiency=1.0,
            pmin=0,
            pmax=50,
            cost_per_mwh=0.0,
            allocated_power=30.0,
        ),
    ]


@pytest.fixture(
    params=[
        ("payload1.json", PAYLOAD1),
        ("payload2.json", PAYLOAD2),
        ("payload3.json", PAYLOAD3),
    ]
)
def example_payload(request):
    """Parametrized fixture for all example payloads."""
    filename, payload = request.param
    return {"filename": filename, "payload": payload}


@pytest.fixture
def payload1():
    """Fixture for payload1.json."""
    return PAYLOAD1


@pytest.fixture
def payload2():
    """Fixture for payload2.json."""
    return PAYLOAD2


@pytest.fixture
def payload3():
    """Fixture for payload3.json."""
    return PAYLOAD3


@pytest.fixture
def expected_response3():
    """Fixture for expected response3.json."""
    return RESPONSE3


# Parametrize data using example payloads
PAYLOAD_PARAMS = [
    ("payload1.json", PAYLOAD1),
    ("payload2.json", PAYLOAD2),
    ("payload3.json", PAYLOAD3),
]

# Parametrize data for cost calculation tests from payloads
COST_CALCULATION_PARAMS = []
for payload_name, payload in PAYLOAD_PARAMS:
    fuels = payload["fuels"]
    for powerplant in payload["powerplants"]:
        # Calculate expected cost based on powerplant type
        if powerplant["type"] == "windturbine":
            expected_cost = 0.0
        elif powerplant["type"] == "gasfired":
            gas_price = fuels["gas(euro/MWh)"]
            co2_price = fuels["co2(euro/ton)"]
            efficiency = powerplant["efficiency"]
            expected_cost = (gas_price / efficiency) + (co2_price * 0.3 / efficiency)
        elif powerplant["type"] == "turbojet":
            kerosine_price = fuels["kerosine(euro/MWh)"]
            efficiency = powerplant["efficiency"]
            expected_cost = kerosine_price / efficiency

        COST_CALCULATION_PARAMS.append(
            (
                powerplant["name"],
                powerplant["type"],
                powerplant["efficiency"],
                powerplant["pmin"],
                powerplant["pmax"],
                fuels["gas(euro/MWh)"],
                fuels["kerosine(euro/MWh)"],
                fuels["co2(euro/ton)"],
                fuels["wind(%)"],
                expected_cost,
                f"{powerplant['type']} from {payload_name}",
            )
        )
