import pytest

from conftest import set_status

ALL_VINS = [f"WDD213141516{i}" for i in range(1, 6)]
ENGINE_TYPES = {
    "WDD2131415161": "Electric Vehicle",
    "WDD2131415162": "Internal Combustion Engine Vehicle",
    "WDD2131415163": "Hybrid Electric Vehicle",
    "WDD2131415164": "Plug-in Hybrid Electric Vehicle",
    "WDD2131415165": "Fuel Cell Electric Vehicle",
}


@pytest.mark.parametrize("vin", ALL_VINS)
def test_every_predefined_vehicle_has_info_and_default_status(client, vin):
    info = client.get(f"/{vin}/info")
    assert info.status_code == 200
    assert info.json()["Engine Type"] == ENGINE_TYPES[vin]

    status = client.get(f"/{vin}/status")
    assert status.status_code == 200
    assert status.json()["mileage"] == 0


def test_unknown_vin_returns_404(client):
    assert client.get("/UNKNOWN/info").status_code == 404
    assert client.get("/UNKNOWN/status").status_code == 404
    assert client.post("/UNKNOWN/status", json={"mileage": 1}).status_code == 404


def test_status_update_roundtrip(client, vin):
    set_status(client, vin, fuel_level=80, tyre_fl=2.4, door_status="Closed", door_lock_status="Locked")
    status = client.get(f"/{vin}/status").json()
    assert status["mileage"] == 1000
    assert status["fuel_level"] == 80
    assert status["tyre_fl"] == 2.4
    assert status["door_lock_status"] == "Locked"


@pytest.mark.parametrize(
    "bad_body",
    [
        {"mileage": -1},
        {"mileage": 10, "fuel_level": 101},
        {"mileage": 10, "fuel_level": -5},
        {"mileage": 10, "consumption": -0.1},
        {"mileage": 10, "range_km": -1},
        {},
    ],
)
def test_invalid_status_is_rejected(client, vin, bad_body):
    assert client.post(f"/{vin}/status", json=bad_body).status_code == 422


def test_override_default_is_empty_and_roundtrips(client, vin):
    assert client.get(f"/{vin}/override").json()["lock_doors"] is None

    client.post(f"/{vin}/override", json={"lock_doors": "failed", "open_windows": "success"})
    override = client.get(f"/{vin}/override").json()
    assert override["lock_doors"] == "failed"
    assert override["open_windows"] == "success"
    assert override["unlock_doors"] is None
