"""Shared fixtures: every test gets a fresh app with its own empty SQLite database."""
import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SIM_DIR = Path(__file__).resolve().parent.parent
VIN = "WDD2131415161"


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    """Import main.py inside a temp directory so vehicles.db is created there."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(SIM_DIR))
    sys.modules.pop("main", None)
    module = importlib.import_module("main")
    # Commands sleep 2-15 s to simulate network delay; skip the wait in tests.
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    yield module
    sys.modules.pop("main", None)


@pytest.fixture()
def client(app_module):
    return TestClient(app_module.app)


@pytest.fixture()
def vin():
    return VIN


def set_status(client, vin=VIN, **fields):
    """Helper: update a vehicle status (mileage is required by the API)."""
    body = {"mileage": 1000, **fields}
    response = client.post(f"/{vin}/status", json=body)
    assert response.status_code == 200
    return response


def send(client, command, vin=VIN, delay=2):
    return client.post(f"/{vin}/command", json={"command": command, "test_delay": delay}).json()
