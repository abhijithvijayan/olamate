import json
from typing import Any

CELL_COUNT = 14
BALANCE_THRESHOLD_MV = 20.0
COLLECTOR_STALE_AFTER_S = 5.0


def cell_report(row: dict[str, Any]) -> dict[str, Any]:
    voltages = [row.get(f"cell_{i}") for i in range(1, CELL_COUNT + 1)]
    valid = [v for v in voltages if v is not None and v > 0]
    if not valid:
        return {
            "timestamp": row.get("timestamp"),
            "cells": [],
            "min": None,
            "max": None,
            "avg": None,
            "spread_mV": None,
            "balancing_needed": False,
        }

    avg = sum(valid) / len(valid)
    vmin, vmax = min(valid), max(valid)
    cells = []
    for i, v in enumerate(voltages, start=1):
        if v is None or v <= 0:
            cells.append({"index": i, "voltage": None, "deviation_mV": None, "state": "missing"})
            continue
        dev = round((v - avg) * 1000, 1)
        if abs(dev) > BALANCE_THRESHOLD_MV:
            state = "high" if dev > 0 else "low"
        else:
            state = "ok"
        cells.append({"index": i, "voltage": v, "deviation_mV": dev, "state": state})

    return {
        "timestamp": row.get("timestamp"),
        "cells": cells,
        "min": vmin,
        "max": vmax,
        "avg": round(avg, 4),
        "spread_mV": round((vmax - vmin) * 1000, 1),
        "balancing_needed": any(c["state"] in ("high", "low") for c in cells),
    }


def parse_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    raw = out.pop("cells_json", None)
    try:
        out["cells"] = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        out["cells"] = []
    return out


def finalize_session(row: dict[str, Any]) -> dict[str, Any]:
    """Fill in derived fields the collector may not have written yet."""
    s = dict(row)
    agg_distance = s.pop("agg_distance_m", None)
    agg_avg_speed = s.pop("agg_avg_speed", None)
    agg_max_speed = s.pop("agg_max_speed", None)
    agg_avg_temp = s.pop("agg_avg_temp", None)
    agg_max_temp = s.pop("agg_max_temp", None)
    agg_avg_power = s.pop("agg_avg_power_w", None)
    agg_last_ts = s.pop("agg_last_ts", None)
    agg_start_soc = s.pop("agg_start_soc", None)
    agg_end_soc = s.pop("agg_end_soc", None)
    agg_drive_mode = s.pop("agg_drive_mode", None)

    in_progress = s.get("end_time") is None
    effective_end = s["end_time"] if not in_progress else (agg_last_ts or s["start_time"])
    duration_s = max(0.0, float(effective_end) - float(s["start_time"]))

    if s.get("start_soc") is None:
        s["start_soc"] = agg_start_soc
    if s.get("end_soc") is None:
        s["end_soc"] = agg_end_soc

    if s.get("distance_m") is None:
        if s.get("start_odometer") is not None and s.get("end_odometer") is not None:
            s["distance_m"] = max(0, int(s["end_odometer"]) - int(s["start_odometer"]))
        elif agg_distance is not None:
            s["distance_m"] = max(0, int(agg_distance))

    if s.get("avg_speed") is None and agg_avg_speed is not None:
        s["avg_speed"] = round(agg_avg_speed, 1)
    if s.get("max_speed") is None and agg_max_speed is not None:
        s["max_speed"] = round(agg_max_speed, 1)
    if s.get("avg_temp") is None and agg_avg_temp is not None:
        s["avg_temp"] = round(agg_avg_temp, 1)
    if s.get("max_temp") is None and agg_max_temp is not None:
        s["max_temp"] = round(agg_max_temp, 1)
    if s.get("energy_wh") is None and agg_avg_power is not None and duration_s > 0:
        s["energy_wh"] = round(abs(agg_avg_power) * duration_s / 3600.0, 1)

    soc_delta = None
    if s.get("start_soc") is not None and s.get("end_soc") is not None:
        soc_delta = round(float(s["end_soc"]) - float(s["start_soc"]), 1)

    efficiency = None
    if s.get("energy_wh") and s.get("distance_m"):
        km = s["distance_m"] / 1000.0
        if km >= 0.1:
            efficiency = round(s["energy_wh"] / km, 1)

    DRIVE_MODE_NAMES = {0: "Parked", 2: "Normal", 3: "Sport", 4: "Custom",
                        5: "Reverse", 6: "Eco", 7: "Hyper", 10: "Reverse", 13: "Reverse"}
    drive_mode_raw = agg_drive_mode if agg_drive_mode is not None else s.get("drive_mode")
    drive_mode_int = int(drive_mode_raw) if drive_mode_raw is not None else None

    s["in_progress"] = in_progress
    s["duration_s"] = round(duration_s, 1)
    s["soc_delta"] = soc_delta
    s["efficiency_wh_per_km"] = efficiency
    s["drive_mode"] = drive_mode_int
    s["drive_mode_name"] = DRIVE_MODE_NAMES.get(drive_mode_int, None) if drive_mode_int is not None else None
    return s


def downsample(rows: list[dict[str, Any]], max_points: int) -> list[dict[str, Any]]:
    if max_points <= 0 or len(rows) <= max_points:
        return rows
    step = len(rows) / max_points
    picked = [rows[int(i * step)] for i in range(max_points)]
    if picked[-1] is not rows[-1]:
        picked[-1] = rows[-1]
    return picked
