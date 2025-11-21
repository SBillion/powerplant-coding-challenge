from typing import Literal
from pydantic import BaseModel, Field


class FuelPrices(BaseModel):
    gas: float = Field(alias="gas(euro/MWh)", description="Price of gas per MWh")
    kerosine: float = Field(
        alias="kerosine(euro/MWh)", description="Price of kerosine per MWh"
    )
    co2: float = Field(alias="co2(euro/ton)", description="Price of CO2 per ton")
    wind: float = Field(
        alias="wind(%)",
        description="Wind availability as a percentage (0-100)",
        ge=0,
        le=100,
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "gas": 13.4,
                    "kerosine": 50.8,
                    "co2": 20,
                    "wind": 60,
                },
                {
                    "gas(euro/MWh)": 22.4,
                    "kerosine(euro/MWh)": 70.8,
                    "co2(euro/ton)": 25,
                    "wind(%)": 45,
                },
            ],
        },
    }


class PowerPlant(BaseModel):
    name: str
    type: Literal["gasfired", "turbojet", "windturbine"] = Field(
        description="Type of powerplant"
    )

    efficiency: float = Field(
        description="Efficiency of the powerplant (0-1)", ge=0, le=1
    )

    pmin: float = Field(description="Minimum power output (MW)", ge=0)
    pmax: float = Field(description="Maximum power output (MW)", gt=0)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Gasfire1",
                    "type": "gasfired",
                    "efficiency": 0.53,
                    "pmin": 100,
                    "pmax": 460,
                }
            ]
        }
    }


class PowerPlantWithCostAndPower(PowerPlant):
    cost_per_mwh: float
    allocated_power: float = 0.0
