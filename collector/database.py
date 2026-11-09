"""
SQLite database layer for OlaMate telemetry storage.
"""

import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "./olamate.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    session_id INTEGER,

    -- Battery pack
    soc REAL,
    soh REAL,
    voltage REAL,
    current REAL,
    regen_power_limit REAL,
    discharge_power_limit REAL,

    -- Cell voltages (14S)
    cell_1 REAL, cell_2 REAL, cell_3 REAL, cell_4 REAL,
    cell_5 REAL, cell_6 REAL, cell_7 REAL, cell_8 REAL,
    cell_9 REAL, cell_10 REAL, cell_11 REAL, cell_12 REAL,
    cell_13 REAL, cell_14 REAL,
    cell_min REAL,
    cell_max REAL,
    cell_spread_mV REAL,

    -- Temperatures
    temp_effective REAL,
    temp_min REAL,
    temp_max REAL,
    temp_pack_1 REAL, temp_pack_2 REAL, temp_pack_3 REAL,
    temp_pack_4 REAL, temp_pack_5 REAL, temp_pack_6 REAL,
    temp_mcu REAL,
    temp_motor REAL,

    -- Motor/driving
    speed REAL,
    motor_rpm INTEGER,
    odometer INTEGER,

    -- Range
    range_normal INTEGER,
    range_sport INTEGER,
    range_hyper INTEGER,

    -- Status
    side_stand INTEGER,
    regen_availability INTEGER,
    hill_hold INTEGER,
    drive_mode INTEGER  -- 0=Parked,2=Normal,3=Sport,6=Eco,7=Hyper
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,  -- 'ride' or 'charge'
    start_time REAL NOT NULL,
    end_time REAL,
    start_soc REAL,
    end_soc REAL,
    start_odometer INTEGER,
    end_odometer INTEGER,
    distance_m INTEGER,
    energy_wh REAL,
    avg_speed REAL,
    max_speed REAL,
    avg_temp REAL,
    max_temp REAL
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    soc REAL,
    soh REAL,
    voltage REAL,
    cell_spread_mV REAL,
    odometer INTEGER,
    temp_effective REAL,
    cells_json TEXT  -- JSON array of 14 cell voltages
);

CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp);
CREATE INDEX IF NOT EXISTS idx_telemetry_session ON telemetry(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time);
CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp);
"""


def init_db(db_path: str = DB_PATH) -> None:
    """Create tables if they don't exist."""
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_db(db_path: str = DB_PATH):
    """Context manager for database connections."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def insert_telemetry(conn: sqlite3.Connection, data: dict) -> int:
    """Insert a telemetry row. Returns the row ID."""
    columns = [k for k in data.keys() if k != "id"]
    placeholders = ", ".join(["?"] * len(columns))
    col_names = ", ".join(columns)
    values = [data[k] for k in columns]

    cursor = conn.execute(
        f"INSERT INTO telemetry ({col_names}) VALUES ({placeholders})",
        values,
    )
    return cursor.lastrowid


def insert_snapshot(conn: sqlite3.Connection, data: dict) -> int:
    """Insert a health snapshot row."""
    columns = list(data.keys())
    placeholders = ", ".join(["?"] * len(columns))
    col_names = ", ".join(columns)
    values = [data[k] for k in columns]

    cursor = conn.execute(
        f"INSERT INTO snapshots ({col_names}) VALUES ({placeholders})",
        values,
    )
    return cursor.lastrowid


def start_session(conn: sqlite3.Connection, session_type: str, start_time: float, start_soc: float = None, start_odometer: int = None) -> int:
    """Start a new ride or charge session. Returns session ID."""
    cursor = conn.execute(
        "INSERT INTO sessions (type, start_time, start_soc, start_odometer) VALUES (?, ?, ?, ?)",
        (session_type, start_time, start_soc, start_odometer),
    )
    return cursor.lastrowid


def end_session(conn: sqlite3.Connection, session_id: int, **kwargs) -> None:
    """End a session with summary data."""
    sets = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [session_id]
    conn.execute(f"UPDATE sessions SET {sets} WHERE id = ?", values)
