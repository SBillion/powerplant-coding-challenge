from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["message"] == "Powerplant Production Plan API is running"
    assert data["version"] == "0.1.0"


def test_production_plan_not_empty_response():
    payload = {
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

    response = client.post("/productionplan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data != []  # Placeholder check since implementation is not complete
