# Simulation Environment for Testing Connected Cars

Master's thesis project, M.Eng. Software-based Automotive Systems, Hochschule Esslingen (2025).

A web-based software-in-the-loop (SiL) simulator for testing how a connected-car application behaves when it sends remote commands (lock, unlock, open and close windows) to a vehicle backend. No vehicle or test bench is needed. The simulator can answer with success, a specific failure, or a timeout, so that an app's error handling can be tested on demand.

## What it does

- **Simulated vehicle backend** (FastAPI) with five fictional vehicles, each with its own VIN and engine type: electric, internal combustion, hybrid, plug-in hybrid and fuel cell.
- **Vehicle status** per VIN: mileage, tyre pressures, fuel level, range, consumption, service and coolant status, door, window and lock state. Inputs are validated (for example, mileage cannot be negative and fuel level must be 0 to 100).
- **Remote commands** with realistic behaviour: `lock_doors`, `unlock_doors`, `open_windows`, `close_windows`.
  - The result depends on the vehicle state. Locking fails with `DOOR_OPEN` if a door is open and with `IGNITION_ON` if the engine is running. Unlocking an unlocked car fails with `ALREADY_UNLOCKED`, and the window commands fail with `ALREADY_OPENED` or `ALREADY_CLOSED`.
  - Every command runs with a delay of 2, 5 or 15 seconds (random, or set with `test_delay`). A delay of 15 seconds returns `timeout`, which simulates a network or vehicle that does not answer in time.
  - Unknown commands return `UNKNOWN_COMMAND`.
- **Command overrides**: for any VIN and command you can force the result to `success` or `failed`, regardless of the vehicle state. This makes edge cases repeatable in a test.
- **Two role-separated frontends** that use the same backend:
  - `Frontend.html`, the **Vehicle Manager**: edit a vehicle's status values and set command overrides.
  - `Second_Frontend.html`, the **Vehicle Status Dashboard**: view the current status and send commands, as the connected-car app would.

## Architecture

```
 Vehicle Manager (Frontend.html)  ──┐
                                    ├──  FastAPI backend (main.py)  ──  SQLite (vehicles.db)
 Status Dashboard (Second_Frontend) ─┘      status, override, command logic
```

| Method and path | Purpose |
|---|---|
| `GET /{vin}/info` | Vehicle data (make, model, colour, doors, windows, engine type) |
| `GET /{vin}/status` | Current vehicle status |
| `POST /{vin}/status` | Create or update the vehicle status |
| `GET /{vin}/override` | Current command overrides |
| `POST /{vin}/override` | Set command overrides (`success`, `failed` or empty) |
| `POST /{vin}/command` | Execute a command, for example `{"command": "lock_doors", "test_delay": 2}` |

The interactive API documentation is generated automatically at `http://localhost:8000/docs`.

## Run it locally

You need Python 3.10 or newer.

```bash
cd connected-car-sim
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

Then open `Frontend.html` and `Second_Frontend.html` in a browser. The frontends call the backend at `http://localhost:8000`.

The SQLite database `vehicles.db` is created automatically on the first start.

### Quick test without the frontends

```bash
# Set the vehicle state
curl -X POST localhost:8000/WDD2131415162/status -H 'content-type: application/json' \
  -d '{"mileage":1200,"door_status":"Open","door_lock_status":"Unlocked"}'

# Try to lock it: fails with DOOR_OPEN
curl -X POST localhost:8000/WDD2131415162/command -H 'content-type: application/json' \
  -d '{"command":"lock_doors","test_delay":2}'
```

## Tech stack

Python, FastAPI, Pydantic, SQLite, Uvicorn, HTML, CSS and JavaScript (Fetch API).

## Notes

- All vehicles, VINs and values are fictional test data.
- CORS is open (`*`) and there is no authentication. The project is meant for local testing only, not for deployment.
- The frontends load the car-brand logos from external image hosts, so the logos only appear when you are online.
- Vehicle makes and logos belong to their owners and are only used as labels in this demo.
