"""
Generate a synthetic olamate.db so the API and dashboard can be developed
without the scooter. Rides and charges are shaped loosely like real data.

Usage:
    python scripts/seed_demo.py [path/to/olamate.db]
"""

import json
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collector.database import (  # noqa: E402
    end_session,
    get_db,
    init_db,
    insert_snapshot,
    insert_telemetry,
    start_session,
)

CELL_NOMINAL = 3.95


def _cells(soc: float, rng: random.Random, spread_mv: float) -> list[float]:
    base = 3.45 + 0.75 * (soc / 100.0)
    return [round(base + rng.uniform(-spread_mv, spread_mv) / 2000.0, 3) for _ in range(14)]


def _row(ts: float, session_id: int | None, soc: float, speed: float, odo: int,
         current: float, temp: float, rng: random.Random, soh: float) -> dict:
    cells = _cells(soc, rng, spread_mv=14 + rng.uniform(0, 10))
    voltage = round(sum(cells), 2)
    row = {
        "timestamp": ts,
        "session_id": session_id,
        "soc": round(soc, 1),
        "soh": soh,
        "voltage": voltage,
        "current": round(current, 2),
        "regen_power_limit": 1500,
        "discharge_power_limit": 8500,
        "cell_min": min(cells),
        "cell_max": max(cells),
        "cell_spread_mV": round((max(cells) - min(cells)) * 1000, 1),
        "temp_effective": round(temp, 1),
        "temp_min": round(temp - 1.5, 1),
        "temp_max": round(temp + 2.0, 1),
        "temp_mcu": round(temp + 8 + speed * 0.2, 1),
        "temp_motor": round(temp + 12 + speed * 0.35, 1),
        "speed": round(speed, 1),
        "motor_rpm": int(speed * 95),
        "odometer": odo,
        "range_normal": int(soc * 1.2),
        "range_sport": int(soc * 0.95),
        "range_hyper": int(soc * 0.75),
        "side_stand": 0 if speed > 0 else 1,
        "regen_availability": 1,
        "hill_hold": 0,
    }
    for i, v in enumerate(cells, start=1):
        row[f"cell_{i}"] = v
    for i in range(1, 7):
        row[f"temp_pack_{i}"] = round(temp + rng.uniform(-1.5, 2.5), 1)
    return row


def seed(db_path: str, days: int = 14, seed_value: int = 7) -> None:
    rng = random.Random(seed_value)
    init_db(db_path)
    now = time.time()
    t = now - days * 86400
    soc = 92.0
    odo = 4_210_000
    soh = 97.0

    with get_db(db_path) as conn:
        while t < now - 8 * 3600:
            kind = "ride" if soc > 25 else "charge"
            if kind == "ride":
                minutes = rng.uniform(8, 45)
                sid = start_session(conn, "ride", t, start_soc=soc, start_odometer=odo)
                start_odo = odo
                temp = 29 + rng.uniform(-3, 4)
                max_speed = 0.0
                speeds = []
                for sec in range(0, int(minutes * 60), 1):
                    if soc <= 4:
                        break
                    phase = sec / (minutes * 60)
                    speed = max(0.0, 40 + 25 * math.sin(phase * math.pi * 3) + rng.uniform(-6, 6))
                    if phase < 0.02 or phase > 0.98:
                        speed = speed * phase * 20 if phase < 0.02 else speed * (1 - phase) * 20
                    current = 15 + speed * 0.9 + rng.uniform(-4, 4)
                    odo += int(speed / 3.6)
                    soc -= (current * 52 / 3600) / 2900 * 100
                    temp += 0.0015 * speed / 40
                    speeds.append(speed)
                    max_speed = max(max_speed, speed)
                    insert_telemetry(conn, _row(t + sec, sid, soc, speed, odo, current, temp, rng, soh))
                t += sec
                moving = [s for s in speeds if s > 0]
                end_session(
                    conn, sid, end_time=t, end_soc=round(soc, 1), end_odometer=odo,
                    distance_m=odo - start_odo,
                    avg_speed=round(sum(moving) / len(moving), 1) if moving else 0,
                    max_speed=round(max_speed, 1),
                )
                t += rng.uniform(1, 6) * 3600
            else:
                sid = start_session(conn, "charge", t, start_soc=soc, start_odometer=odo)
                target = rng.choice([80, 90, 100])
                temp = 30 + rng.uniform(-2, 3)
                sec = 0
                while soc < target:
                    current = -(15.0 if soc < 85 else 15.0 * (100 - soc) / 15 + 0.8)
                    soc += abs(current) * 52 / 3600 / 2900 * 100 * 1.0
                    temp += 0.0004
                    if sec % 10 == 0:
                        insert_telemetry(conn, _row(t + sec, sid, min(soc, 100), 0, odo, current, temp, rng, soh))
                    sec += 1
                t += sec
                end_session(conn, sid, end_time=t, end_soc=round(min(soc, 100), 1), end_odometer=odo)
                t += rng.uniform(4, 12) * 3600

            if rng.random() < 0.08 and soh > 94:
                soh = round(soh - 0.5, 1)

        snap_t = now - days * 86400
        snap_soh = 97.5
        snap_odo = 4_205_000
        while snap_t < now:
            cells = _cells(70, rng, spread_mv=12 + (now - snap_t) / 86400 * 0.6)
            insert_snapshot(conn, {
                "timestamp": snap_t,
                "soc": round(rng.uniform(30, 95), 1),
                "soh": snap_soh,
                "voltage": round(sum(cells), 2),
                "cell_spread_mV": round((max(cells) - min(cells)) * 1000, 1),
                "odometer": snap_odo,
                "temp_effective": round(rng.uniform(27, 34), 1),
                "cells_json": json.dumps(cells),
            })
            snap_t += 6 * 3600
            snap_odo += int(rng.uniform(2000, 9000))
            if rng.random() < 0.1:
                snap_soh = round(snap_soh - 0.5, 1)

        for sec in range(0, 60):
            insert_telemetry(conn, _row(now - 60 + sec, None, soc, 0, odo, 0.4, 31.2, rng, soh))


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "olamate.db"
    seed(path)
    print(f"Seeded demo data into {path}")
