import time
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from db import DB_PATH, db_exists, fetch_all, fetch_one
from metrics import (
    COLLECTOR_STALE_AFTER_S,
    cell_report,
    downsample,
    finalize_session,
    parse_snapshot,
)

app = FastAPI(title="OlaMate API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
    allow_methods=["GET"],
    allow_headers=["*"],
)

SESSION_SQL = """
SELECT s.*,
       MAX(t.odometer) - MIN(t.odometer) AS agg_distance_m,
       AVG(CASE WHEN t.speed > 0 THEN t.speed END) AS agg_avg_speed,
       MAX(t.speed) AS agg_max_speed,
       AVG(t.temp_effective) AS agg_avg_temp,
       MAX(t.temp_effective) AS agg_max_temp,
       AVG(t.voltage * t.current) AS agg_avg_power_w,
       MAX(t.timestamp) AS agg_last_ts,
       (SELECT soc FROM telemetry WHERE session_id = s.id ORDER BY timestamp ASC LIMIT 1) AS agg_start_soc,
       (SELECT soc FROM telemetry WHERE session_id = s.id ORDER BY timestamp DESC LIMIT 1) AS agg_end_soc,
       (SELECT drive_mode FROM telemetry WHERE session_id = s.id AND drive_mode IS NOT NULL AND drive_mode != 0 GROUP BY drive_mode ORDER BY COUNT(*) DESC LIMIT 1) AS agg_drive_mode
FROM sessions s
LEFT JOIN telemetry t ON t.session_id = s.id
"""


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "db_path": DB_PATH, "db_exists": db_exists()}


@app.get("/api/status")
async def status() -> dict[str, Any]:
    row = await fetch_one("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 1")
    if row is None:
        raise HTTPException(status_code=404, detail="No telemetry recorded yet")
    age = max(0.0, time.time() - float(row["timestamp"]))
    row["age_seconds"] = round(age, 1)
    row["collector_running"] = age <= COLLECTOR_STALE_AFTER_S
    return row


@app.get("/api/telemetry")
async def telemetry(
    from_ts: float | None = Query(default=None, alias="from"),
    to_ts: float | None = Query(default=None, alias="to"),
    limit: int = Query(default=1000, ge=1, le=10000),
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if from_ts is not None:
        clauses.append("timestamp >= ?")
        params.append(from_ts)
    if to_ts is not None:
        clauses.append("timestamp <= ?")
        params.append(to_ts)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = await fetch_all(
        f"SELECT * FROM (SELECT * FROM telemetry {where} ORDER BY timestamp DESC LIMIT ?) "
        "ORDER BY timestamp ASC",
        (*params, limit),
    )
    return rows


@app.get("/api/sessions")
async def sessions(
    type: Literal["ride", "charge"] | None = None,
    limit: int = Query(default=20, ge=1, le=500),
) -> list[dict[str, Any]]:
    where = "WHERE s.type = ?" if type else ""
    params: tuple[Any, ...] = (type, limit) if type else (limit,)
    rows = await fetch_all(
        f"{SESSION_SQL} {where} GROUP BY s.id ORDER BY s.start_time DESC LIMIT ?",
        params,
    )
    return [finalize_session(r) for r in rows]


@app.get("/api/sessions/{session_id}")
async def session_detail(
    session_id: int,
    points: int = Query(default=600, ge=10, le=10000),
) -> dict[str, Any]:
    row = await fetch_one(f"{SESSION_SQL} WHERE s.id = ? GROUP BY s.id", (session_id,))
    if row is None or row.get("id") is None:
        raise HTTPException(status_code=404, detail="Session not found")
    rows = await fetch_all(
        "SELECT timestamp, soc, voltage, current, speed, motor_rpm, odometer, "
        "temp_effective, temp_motor, temp_mcu, cell_spread_mV, drive_mode "
        "FROM telemetry WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,),
    )
    return {"session": finalize_session(row), "telemetry": downsample(rows, points)}


@app.get("/api/battery/health")
async def battery_health(limit: int = Query(default=30, ge=1, le=1000)) -> dict[str, Any]:
    snaps = await fetch_all(
        "SELECT * FROM (SELECT * FROM snapshots ORDER BY timestamp DESC LIMIT ?) ORDER BY timestamp ASC",
        (limit,),
    )
    source = "snapshots"
    if not snaps:
        source = "telemetry"
        snaps = await fetch_all(
            "SELECT MAX(timestamp) AS timestamp, soc, soh, voltage, cell_spread_mV, odometer, "
            "temp_effective, NULL AS cells_json "
            "FROM telemetry GROUP BY CAST(timestamp / 300 AS INTEGER) ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        snaps.reverse()
    trend = [parse_snapshot(s) for s in snaps]
    latest = trend[-1] if trend else None
    return {"latest": latest, "trend": trend, "source": source}


@app.get("/api/battery/cells")
async def battery_cells() -> dict[str, Any]:
    row = await fetch_one("SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 1")
    if row is None:
        raise HTTPException(status_code=404, detail="No telemetry recorded yet")
    return cell_report(row)


@app.get("/api/stats")
async def stats() -> dict[str, Any]:
    rides = await fetch_all(f"{SESSION_SQL} WHERE s.type = 'ride' GROUP BY s.id")
    charges = await fetch_all(f"{SESSION_SQL} WHERE s.type = 'charge' GROUP BY s.id")
    rides = [finalize_session(r) for r in rides]
    charges = [finalize_session(c) for c in charges]

    completed = [r for r in rides if not r["in_progress"]]
    total_distance = sum(r["distance_m"] or 0 for r in completed)
    total_energy = sum(r["energy_wh"] or 0 for r in completed)
    efficiencies = [r["efficiency_wh_per_km"] for r in completed if r["efficiency_wh_per_km"]]
    durations = [r["duration_s"] for r in completed]

    bounds = await fetch_one(
        "SELECT MIN(timestamp) AS first_seen, MAX(timestamp) AS last_seen, COUNT(*) AS rows_count FROM telemetry"
    )
    latest = await fetch_one("SELECT odometer, soh, soc FROM telemetry ORDER BY timestamp DESC LIMIT 1")

    return {
        "total_rides": len(completed),
        "total_charges": len([c for c in charges if not c["in_progress"]]),
        "total_distance_m": int(total_distance),
        "total_energy_wh": round(total_energy, 1),
        "total_ride_time_s": round(sum(durations), 1),
        "avg_efficiency_wh_per_km": round(sum(efficiencies) / len(efficiencies), 1) if efficiencies else None,
        "avg_ride_distance_m": int(total_distance / len(completed)) if completed else None,
        "longest_ride_m": max((r["distance_m"] or 0 for r in completed), default=None),
        "odometer_m": latest["odometer"] if latest else None,
        "soh": latest["soh"] if latest else None,
        "first_seen": bounds["first_seen"] if bounds else None,
        "last_seen": bounds["last_seen"] if bounds else None,
        "telemetry_rows": bounds["rows_count"] if bounds else 0,
    }
