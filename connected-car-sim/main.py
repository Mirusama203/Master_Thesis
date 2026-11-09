from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sqlite3
import time
from random import choice

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PREDEFINED_VINS = [
    "WDD2131415161",
    "WDD2131415162",
    "WDD2131415163",
    "WDD2131415164",
    "WDD2131415165"
]

VEHICLE_INFO = {
    "WDD2131415161": {"Make": "Mercedes", "Model": "2021", "Color": "Blue", "No of Doors": 4, "Windows": "Auto control", "Engine Type": "Electric Vehicle"},
    "WDD2131415162": {"Make": "BMW", "Model": "2020", "Color": "Red", "No of Doors": 4, "Windows": "Manual", "Engine Type": "Internal Combustion Engine Vehicle"},
    "WDD2131415163": {"Make": "Toyota", "Model": "2022", "Color": "White", "No of Doors": 2, "Windows": "Auto control", "Engine Type": "Hybrid Electric Vehicle"},
    "WDD2131415164": {"Make": "Ford", "Model": "2021", "Color": "Black", "No of Doors": 4, "Windows": "Auto control", "Engine Type": "Plug-in Hybrid Electric Vehicle"},
    "WDD2131415165": {"Make": "Hyundai", "Model": "2023", "Color": "Silver", "No of Doors": 2, "Windows": "Auto control", "Engine Type": "Fuel Cell Electric Vehicle"}
}

def init_db():
    conn = sqlite3.connect("vehicles.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehicles_status (
            vin TEXT PRIMARY KEY,
            mileage INTEGER NOT NULL DEFAULT 0,
            tyre_fl REAL DEFAULT NULL,
            tyre_fr REAL DEFAULT NULL,
            tyre_rl REAL DEFAULT NULL,
            tyre_rr REAL DEFAULT NULL,
            fuel_level INTEGER DEFAULT NULL,
            range_km INTEGER DEFAULT NULL,
            consumption REAL DEFAULT NULL,
            service_status TEXT DEFAULT NULL,
            coolant_status TEXT DEFAULT NULL,
            windows_status TEXT DEFAULT NULL,
            door_status TEXT DEFAULT NULL,
            door_lock_status TEXT DEFAULT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_override (
            vin TEXT PRIMARY KEY,
            lock_doors TEXT DEFAULT NULL,
            unlock_doors TEXT DEFAULT NULL,
            open_windows TEXT DEFAULT NULL,
            close_windows TEXT DEFAULT NULL
        )
    ''')

    for vin in PREDEFINED_VINS:
        cursor.execute('INSERT OR IGNORE INTO vehicles_status (vin, mileage) VALUES (?, 0)', (vin,))
        cursor.execute('INSERT OR IGNORE INTO command_override (vin) VALUES (?)', (vin,))

    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect("vehicles.db")
    conn.row_factory = sqlite3.Row
    return conn

class VehicleStatus(BaseModel):
    mileage: int = Field(ge=0)
    tyre_fl: float | None = None
    tyre_fr: float | None = None
    tyre_rl: float | None = None
    tyre_rr: float | None = None
    fuel_level: int | None = Field(None, ge=0, le=100)
    range_km: int | None = Field(None, ge=0)
    consumption: float | None = Field(None, ge=0)
    service_status: str | None = None
    coolant_status: str | None = None
    windows_status: str | None = None
    door_status: str | None = None
    door_lock_status: str | None = None

class CommandOverride(BaseModel):
    lock_doors: str | None = None
    unlock_doors: str | None = None
    open_windows: str | None = None
    close_windows: str | None = None

@app.get("/{vin}/info")
def get_vehicle_info(vin: str):
    info = VEHICLE_INFO.get(vin)
    if not info:
        raise HTTPException(status_code=404, detail="Vehicle information not found")
    return info

@app.get("/{vin}/status", response_model=VehicleStatus)
def get_vehicle_status(vin: str):
    if vin not in PREDEFINED_VINS:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles_status WHERE vin = ?", (vin,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Status not found")
    return VehicleStatus(**row)

@app.post("/{vin}/status")
def update_vehicle_status(vin: str, status: VehicleStatus):
    if vin not in PREDEFINED_VINS:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO vehicles_status (
            vin, mileage, tyre_fl, tyre_fr, tyre_rl, tyre_rr,
            fuel_level, range_km, consumption, service_status,
            coolant_status, windows_status, door_status, door_lock_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(vin) DO UPDATE SET
            mileage=excluded.mileage,
            tyre_fl=excluded.tyre_fl,
            tyre_fr=excluded.tyre_fr,
            tyre_rl=excluded.tyre_rl,
            tyre_rr=excluded.tyre_rr,
            fuel_level=excluded.fuel_level,
            range_km=excluded.range_km,
            consumption=excluded.consumption,
            service_status=excluded.service_status,
            coolant_status=excluded.coolant_status,
            windows_status=excluded.windows_status,
            door_status=excluded.door_status,
            door_lock_status=excluded.door_lock_status
    ''', (
        vin, status.mileage, status.tyre_fl, status.tyre_fr, status.tyre_rl, status.tyre_rr,
        status.fuel_level, status.range_km, status.consumption, status.service_status,
        status.coolant_status, status.windows_status, status.door_status, status.door_lock_status
    ))
    conn.commit()
    conn.close()
    return {"message": f"Status updated for {vin}"}

@app.get("/{vin}/override", response_model=CommandOverride)
def get_command_override(vin: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM command_override WHERE vin = ?", (vin,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="VIN override not found")
    return CommandOverride(**row)

@app.post("/{vin}/override")
def update_command_override(vin: str, override: CommandOverride):
    if vin not in PREDEFINED_VINS:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO command_override (
            vin, lock_doors, unlock_doors, open_windows, close_windows
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(vin) DO UPDATE SET
            lock_doors=excluded.lock_doors,
            unlock_doors=excluded.unlock_doors,
            open_windows=excluded.open_windows,
            close_windows=excluded.close_windows
    ''', (vin, override.lock_doors, override.unlock_doors, override.open_windows, override.close_windows))
    conn.commit()
    conn.close()
    return {"message": f"Override updated for {vin}"}

@app.post("/{vin}/command")
def execute_vehicle_command(vin: str, payload: dict = Body(...)):
    if vin not in PREDEFINED_VINS:
        raise HTTPException(status_code=404, detail="VIN not recognized")

    command = payload.get("command")
    delay = payload.get("test_delay", choice([2, 5, 15]))

    conn = get_db()
    cursor = conn.cursor()

    # Check override
    cursor.execute("SELECT * FROM command_override WHERE vin = ?", (vin,))
    override_row = cursor.fetchone()
    if override_row and command in override_row.keys() and override_row[command] in ["success", "failed"]:
        result = override_row[command]
        conn.close()
        return {"accepted": True, "result": result, "time": delay}

    # Normal behavior
    cursor.execute("SELECT door_status, windows_status, service_status, door_lock_status FROM vehicles_status WHERE vin = ?", (vin,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"accepted": False, "result": "rejected"}

    door_status = row["door_status"] or "Closed"
    windows_status = row["windows_status"] or "Closed"
    service_status = row["service_status"] or "Off"
    door_lock_status = row["door_lock_status"] or "Unlocked"

    if command == "lock_doors":
        time.sleep(delay)
        if delay == 15:
            return {"accepted": True, "result": "timeout", "time": delay}
        if door_status == "Open":
            conn.close()
            return {"accepted": True, "result": "failed", "error_code": "DOOR_OPEN", "time": delay}
        if service_status == "Engine on":
            conn.close()
            return {"accepted": True, "result": "failed", "error_code": "IGNITION_ON", "time": delay}
        cursor.execute("UPDATE vehicles_status SET door_lock_status = 'Locked' WHERE vin = ?", (vin,))
        conn.commit()
        conn.close()
        return {"accepted": True, "result": "success", "time": delay}

    if command == "unlock_doors":
        if door_lock_status == "Unlocked":
            if delay == 15:
                return {"accepted": True, "result": "timeout", "time": delay}
            conn.close()
            return {"accepted": True, "result": "failed", "error_code": "ALREADY_UNLOCKED", "time": delay}
        time.sleep(delay)
        if delay == 15:
            return {"accepted": True, "result": "timeout", "time": delay}
        cursor.execute("UPDATE vehicles_status SET door_lock_status = 'Unlocked' WHERE vin = ?", (vin,))
        conn.commit()
        conn.close()
        return {"accepted": True, "result": "success", "time": delay}

    if command == "open_windows":
        if windows_status == "Open":
            if delay == 15:
                return {"accepted": True, "result": "timeout", "time": delay}
            conn.close()
            return {"accepted": True, "result": "failed", "error_code": "ALREADY_OPENED", "time": delay}
        time.sleep(delay)
        if delay == 15:
            return {"accepted": True, "result": "timeout", "time": delay}
        cursor.execute("UPDATE vehicles_status SET windows_status = 'Open' WHERE vin = ?", (vin,))
        conn.commit()
        conn.close()
        return {"accepted": True, "result": "success", "time": delay}

    if command == "close_windows":
        if windows_status == "Closed":
            if delay == 15:
                return {"accepted": True, "result": "timeout", "time": delay}
            conn.close()
            return {"accepted": True, "result": "failed", "error_code": "ALREADY_CLOSED", "time": delay}
        time.sleep(delay)
        if delay == 15:
            return {"accepted": True, "result": "timeout", "time": delay}
        cursor.execute("UPDATE vehicles_status SET windows_status = 'Closed' WHERE vin = ?", (vin,))
        conn.commit()
        conn.close()
        return {"accepted": True, "result": "success", "time": delay}

    conn.close()
    return {"accepted": True, "result": "failed", "error_code": "UNKNOWN_COMMAND", "time": delay}
