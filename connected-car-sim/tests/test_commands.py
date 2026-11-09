import pytest

from conftest import send, set_status


# ---- lock_doors ---------------------------------------------------------

def test_lock_succeeds_when_doors_closed_and_engine_off(client, vin):
    set_status(client, vin, door_status="Closed", door_lock_status="Unlocked", service_status="Off")
    result = send(client, "lock_doors")
    assert result["result"] == "success"
    assert client.get(f"/{vin}/status").json()["door_lock_status"] == "Locked"


def test_lock_fails_with_door_open(client, vin):
    set_status(client, vin, door_status="Open", door_lock_status="Unlocked")
    result = send(client, "lock_doors")
    assert result["result"] == "failed"
    assert result["error_code"] == "DOOR_OPEN"
    assert client.get(f"/{vin}/status").json()["door_lock_status"] == "Unlocked"


def test_lock_fails_with_engine_on(client, vin):
    set_status(client, vin, door_status="Closed", service_status="Engine on")
    result = send(client, "lock_doors")
    assert result["result"] == "failed"
    assert result["error_code"] == "IGNITION_ON"


# ---- unlock_doors -------------------------------------------------------

def test_unlock_succeeds_when_locked(client, vin):
    set_status(client, vin, door_lock_status="Locked")
    assert send(client, "unlock_doors")["result"] == "success"
    assert client.get(f"/{vin}/status").json()["door_lock_status"] == "Unlocked"


def test_unlock_fails_when_already_unlocked(client, vin):
    set_status(client, vin, door_lock_status="Unlocked")
    result = send(client, "unlock_doors")
    assert result["result"] == "failed"
    assert result["error_code"] == "ALREADY_UNLOCKED"


# ---- windows ------------------------------------------------------------

def test_open_windows_flow(client, vin):
    set_status(client, vin, windows_status="Closed")
    assert send(client, "open_windows")["result"] == "success"
    again = send(client, "open_windows")
    assert again["result"] == "failed"
    assert again["error_code"] == "ALREADY_OPENED"


def test_close_windows_flow(client, vin):
    set_status(client, vin, windows_status="Open")
    assert send(client, "close_windows")["result"] == "success"
    again = send(client, "close_windows")
    assert again["result"] == "failed"
    assert again["error_code"] == "ALREADY_CLOSED"


# ---- timeouts, unknown commands, unknown vehicle ------------------------

@pytest.mark.parametrize(
    "command, status",
    [
        ("lock_doors", {"door_status": "Closed"}),
        ("unlock_doors", {"door_lock_status": "Locked"}),
        ("open_windows", {"windows_status": "Closed"}),
        ("close_windows", {"windows_status": "Open"}),
    ],
)
def test_delay_of_15_seconds_is_a_timeout(client, vin, command, status):
    set_status(client, vin, **status)
    result = send(client, command, delay=15)
    assert result["result"] == "timeout"
    assert result["time"] == 15


def test_unknown_command_is_reported(client, vin):
    result = send(client, "start_engine")
    assert result["result"] == "failed"
    assert result["error_code"] == "UNKNOWN_COMMAND"


def test_command_for_unknown_vin_returns_404(client):
    response = client.post("/UNKNOWN/command", json={"command": "lock_doors", "test_delay": 2})
    assert response.status_code == 404


def test_response_reports_the_delay_used(client, vin):
    set_status(client, vin, door_lock_status="Locked")
    assert send(client, "unlock_doors", delay=5)["time"] == 5


# ---- overrides ----------------------------------------------------------

def test_override_forces_success_even_when_state_would_fail(client, vin):
    set_status(client, vin, door_status="Open")  # would normally fail with DOOR_OPEN
    client.post(f"/{vin}/override", json={"lock_doors": "success"})
    assert send(client, "lock_doors")["result"] == "success"


def test_override_forces_failure_even_when_state_would_succeed(client, vin):
    set_status(client, vin, door_status="Closed", door_lock_status="Unlocked")
    client.post(f"/{vin}/override", json={"lock_doors": "failed"})
    assert send(client, "lock_doors")["result"] == "failed"


def test_override_only_affects_its_own_command(client, vin):
    set_status(client, vin, door_lock_status="Locked")
    client.post(f"/{vin}/override", json={"lock_doors": "failed"})
    assert send(client, "unlock_doors")["result"] == "success"


def test_clearing_override_restores_normal_behaviour(client, vin):
    set_status(client, vin, door_status="Open")
    client.post(f"/{vin}/override", json={"lock_doors": "success"})
    client.post(f"/{vin}/override", json={})
    assert send(client, "lock_doors")["error_code"] == "DOOR_OPEN"
