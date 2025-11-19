from pydantic import BaseModel, Field
from app.models import FuelPrices, PowerPlant


class ProductionRequest(BaseModel):
    """Request payload for production plan calculation."""

    load: float = Field(
        description="Total load to be distributed among powerplants (MW)", ge=0
    )

    fuels: FuelPrices = Field(description="Current fuel prices and wind availability")
    powerplants: list[PowerPlant] = Field(description="List of available powerplants")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "load": 480,
                    "fuels": {
                        "gas(euros/MWh)": 13.4,
                        "kerosine(euro/MWh)": 50.8,
                        "co2(euro/ton)": 20,
                        "wind(%)": 60,
                    },
                    "powerplants": [
                        {
                            "name": "Gasfire1",
                            "type": "gasfired",
                            "efficiency": 0.53,
                            "pmin": 100,
                            "pmax": 460,
                        },
                        {
                            "name": "Turbojet1",
                            "type": "turbojet",
                            "efficiency": 0.3,
                            "pmin": 0,
                            "pmax": 16,
                        },
                        {
                            "name": "Windpark1",
                            "type": "windturbine",
                            "efficiency": 1,
                            "pmin": 0,
                            "pmax": 150,
                        },
                    ],
                }
            ],
        }
    }


class ProductionResponseItem(BaseModel):
    """Response output for a single powerplant"""

    name: str = Field(description="Name of the powerplant")
    p: float = Field(description="Power output of the powerplant (MW)", ge=0)


class ProductionResponse(list[ProductionResponseItem]):
    """Response payload for all powerplants' production plan."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "Gasfire1", "p": 368.4},
                {"name": "Turbojet1", "p": 0},
                {"name": "Windpark1", "p": 90},
            ],
        }
    }
