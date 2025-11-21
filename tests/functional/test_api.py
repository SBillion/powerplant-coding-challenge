"""Functional tests for the API endpoints."""

import pytest
from tests.functional.conftest import PAYLOAD_TEST_PARAMS


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        """Health endpoint should return status information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["message"] == "Powerplant Production Plan API is running"
        assert data["version"] == "0.1.0"


class TestProductionPlanEndpoint:
    """Tests for the production plan endpoint."""

    @pytest.mark.parametrize("payload_name,payload,expected_load", PAYLOAD_TEST_PARAMS)
    def test_production_plan_with_example_payloads(
        self, client, payload_name, payload, expected_load
    ):
        """Production plan should accept all example payloads and return valid responses."""
        response = client.post("/productionplan", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert isinstance(data, list)
        assert len(data) == len(payload["powerplants"])

        # Validate each powerplant response
        for plant in data:
            assert "name" in plant and "p" in plant
            assert isinstance(plant["p"], (int, float)) and plant["p"] >= 0

        # Validate total power matches load
        total_power = sum(plant["p"] for plant in data)
        assert abs(total_power - expected_load) < 0.1

        # Validate all plant names present
        input_names = {p["name"] for p in payload["powerplants"]}
        output_names = {p["name"] for p in data}
        assert input_names == output_names

    def test_production_plan_payload1_high_wind(self, client, payload1):
        """Payload1 with 60% wind should prioritize wind turbines."""
        response = client.post("/productionplan", json=payload1)
        assert response.status_code == 200

        data = response.json()
        wind_names = {
            p["name"] for p in payload1["powerplants"] if p["type"] == "windturbine"
        }
        wind_power = sum(p["p"] for p in data if p["name"] in wind_names)

        assert wind_power > 0

    def test_production_plan_payload2_no_wind(self, client, payload2):
        """Payload2 with 0% wind should not use wind turbines."""
        response = client.post("/productionplan", json=payload2)
        assert response.status_code == 200

        data = response.json()
        wind_names = {
            p["name"] for p in payload2["powerplants"] if p["type"] == "windturbine"
        }

        for plant in data:
            if plant["name"] in wind_names:
                assert plant["p"] == 0

    def test_production_plan_payload3_with_expected_response(
        self, client, payload3, expected_response3
    ):
        """Payload3 should produce the expected response."""
        response = client.post("/productionplan", json=payload3)
        assert response.status_code == 200

        data = response.json()
        assert len(data) == len(expected_response3)

        actual = {p["name"]: p["p"] for p in data}
        expected = {p["name"]: p["p"] for p in expected_response3}

        for name, expected_power in expected.items():
            assert name in actual
            assert abs(actual[name] - expected_power) < 0.1

    def test_production_plan_validates_power_constraints(self, client):
        """Production plan should respect pmin and pmax constraints."""
        payload = {
            "load": 150,
            "fuels": {
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20,
                "wind(%)": 0,
            },
            "powerplants": [
                {
                    "name": "plant1",
                    "type": "gasfired",
                    "efficiency": 0.5,
                    "pmin": 40,
                    "pmax": 200,
                }
            ],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 200

        power = response.json()[0]["p"]
        if power > 0:
            assert 40 <= power <= 200

    def test_production_plan_merit_order_cheapest_first(self, client):
        """Production plan should prioritize plants by merit order (cost)."""
        payload = {
            "load": 100,
            "fuels": {
                "gas(euro/MWh)": 30.0,
                "kerosine(euro/MWh)": 80.0,
                "co2(euro/ton)": 20,
                "wind(%)": 60,
            },
            "powerplants": [
                {
                    "name": "expensive_gas",
                    "type": "gasfired",
                    "efficiency": 0.4,
                    "pmin": 0,
                    "pmax": 200,
                },
                {
                    "name": "cheap_wind",
                    "type": "windturbine",
                    "efficiency": 1.0,
                    "pmin": 0,
                    "pmax": 150,
                },
                {
                    "name": "expensive_jet",
                    "type": "turbojet",
                    "efficiency": 0.3,
                    "pmin": 0,
                    "pmax": 50,
                },
            ],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 200

        data = response.json()
        wind_power = next(p["p"] for p in data if p["name"] == "cheap_wind")
        assert wind_power > 0

        total_power = sum(p["p"] for p in data)
        assert abs(total_power - 100) < 0.1


class TestProductionPlanValidation:
    """Tests for input validation."""

    def test_production_plan_missing_load(self, client):
        """Request without load should return validation error."""
        payload = {
            "fuels": {
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20,
                "wind(%)": 60,
            },
            "powerplants": [],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 422  # Validation error

    def test_production_plan_negative_load(self, client):
        """Request with negative load should return validation error."""
        payload = {
            "load": -100,
            "fuels": {
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20,
                "wind(%)": 60,
            },
            "powerplants": [],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 422  # Validation error

    def test_production_plan_missing_fuels(self, client):
        """Request without fuels should return validation error."""
        payload = {
            "load": 100,
            "powerplants": [],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 422  # Validation error

    def test_production_plan_invalid_wind_percentage(self, client):
        """Request with wind > 100% should return validation error."""
        payload = {
            "load": 100,
            "fuels": {
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20,
                "wind(%)": 150,  # Invalid: > 100
            },
            "powerplants": [],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 422  # Validation error

    def test_production_plan_empty_powerplants(self, client):
        """Request with no powerplants should fail due to insufficient capacity."""
        payload = {
            "load": 100,
            "fuels": {
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20,
                "wind(%)": 60,
            },
            "powerplants": [],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 400

    def test_production_plan_invalid_plant_type(self, client):
        """Request with invalid powerplant type should return validation error."""
        payload = {
            "load": 100,
            "fuels": {
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20,
                "wind(%)": 60,
            },
            "powerplants": [
                {
                    "name": "nuclear1",
                    "type": "nuclear",  # Invalid type
                    "efficiency": 0.9,
                    "pmin": 100,
                    "pmax": 500,
                }
            ],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 422  # Validation error


class TestProductionPlanEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_production_plan_zero_load(self, client):
        """Request with zero load should allocate zero power to all plants."""
        payload = {
            "load": 0,
            "fuels": {
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20,
                "wind(%)": 60,
            },
            "powerplants": [
                {
                    "name": "plant1",
                    "type": "gasfired",
                    "efficiency": 0.5,
                    "pmin": 40,
                    "pmax": 200,
                }
            ],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 200
        assert sum(p["p"] for p in response.json()) == 0

    def test_production_plan_load_below_all_pmin(self, client):
        """Request where load is less than minimum power of all plants should fail."""
        payload = {
            "load": 50,
            "fuels": {
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20,
                "wind(%)": 0,
            },
            "powerplants": [
                {
                    "name": "plant1",
                    "type": "gasfired",
                    "efficiency": 0.5,
                    "pmin": 100,
                    "pmax": 200,
                }
            ],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 400

    def test_production_plan_exact_pmin_match(self, client):
        """Request where load exactly matches a powerplant's pmin."""
        payload = {
            "load": 100,
            "fuels": {
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20,
                "wind(%)": 0,
            },
            "powerplants": [
                {
                    "name": "plant1",
                    "type": "gasfired",
                    "efficiency": 0.5,
                    "pmin": 100,
                    "pmax": 200,
                }
            ],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 200
        assert response.json()[0]["p"] == 100

    def test_production_plan_multiple_solutions(self, client):
        """Request where multiple powerplant combinations could satisfy the load."""
        payload = {
            "load": 100,
            "fuels": {
                "gas(euro/MWh)": 20.0,
                "kerosine(euro/MWh)": 50.0,
                "co2(euro/ton)": 10,
                "wind(%)": 0,
            },
            "powerplants": [
                {
                    "name": "plant1",
                    "type": "gasfired",
                    "efficiency": 0.5,
                    "pmin": 0,
                    "pmax": 100,
                },
                {
                    "name": "plant2",
                    "type": "gasfired",
                    "efficiency": 0.5,
                    "pmin": 0,
                    "pmax": 100,
                },
            ],
        }

        response = client.post("/productionplan", json=payload)
        assert response.status_code == 200

        total_power = sum(p["p"] for p in response.json())
        assert abs(total_power - 100) < 0.1
