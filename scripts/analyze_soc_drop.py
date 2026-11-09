"""
Analyze SOC drop events — finds the moment SOC crashes and shows
which cell hit the floor first.

Usage:
    python scripts/analyze_soc_drop.py [path/to/olamate.db]
"""

import sqlite3
import sys
from pathlib import Path

db_path = sys.argv[1] if len(sys.argv) > 1 else "olamate.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

CELLS = [f"cell_{i}" for i in range(1, 15)]

# Find all sudden SOC drops (>5% in one step)
rows = conn.execute("""
    SELECT t1.id, t1.timestamp, t1.soc AS soc_after, t2.soc AS soc_before,
           t2.soc - t1.soc AS drop_size
    FROM telemetry t1
    JOIN telemetry t2 ON t2.id = (
        SELECT id FROM telemetry WHERE id < t1.id ORDER BY id DESC LIMIT 1
    )
    WHERE t2.soc - t1.soc > 5
      AND t1.soc IS NOT NULL AND t2.soc IS NOT NULL
    ORDER BY t1.timestamp DESC
    LIMIT 20
""").fetchall()

if not rows:
    print("No sudden SOC drops found yet.")
    print("Keep the collector running during a ride that goes below 20%.")
    print(f"\nCurrent data range:")
    bounds = conn.execute("SELECT MIN(soc), MAX(soc), COUNT(*) FROM telemetry WHERE soc IS NOT NULL").fetchone()
    print(f"  SOC range: {bounds[0]:.1f}% – {bounds[1]:.1f}%  ({bounds[2]} rows)")
    sys.exit(0)

print(f"Found {len(rows)} sudden SOC drop(s):\n")

for event in rows:
    print(f"{'='*70}")
    print(f"SOC: {event['soc_before']:.1f}% → {event['soc_after']:.1f}%  (dropped {event['drop_size']:.1f}%)")

    # Get surrounding telemetry (30s before, 10s after)
    window = conn.execute("""
        SELECT * FROM telemetry
        WHERE timestamp BETWEEN ? - 30 AND ? + 10
        ORDER BY timestamp ASC
    """, (event['timestamp'], event['timestamp'])).fetchall()

    if not window:
        print("  No surrounding data found\n")
        continue

    print(f"  Time window: {len(window)} rows around the drop\n")
    print(f"  {'Time':>6s}  {'SOC':>6s}  {'Volt':>6s}  {'Curr':>6s}  {'Spd':>5s}  ", end="")
    print("  ".join(f"C{i:2d}" for i in range(1, 15)))
    print(f"  {'─'*6}  {'─'*6}  {'─'*6}  {'─'*6}  {'─'*5}  ", end="")
    print("  ".join("─" * 4 for _ in range(14)))

    first_ts = window[0]["timestamp"]
    min_cell_voltage = 5.0
    min_cell_id = 0

    for r in window:
        r = dict(r)
        t = r["timestamp"] - first_ts
        soc = r.get("soc") or 0
        v = r.get("voltage") or 0
        curr = r.get("current") or 0
        spd = r.get("speed") or 0

        cells_str = ""
        for i in range(1, 15):
            cv = r.get(f"cell_{i}")
            if cv and cv > 0:
                if cv < min_cell_voltage:
                    min_cell_voltage = cv
                    min_cell_id = i
                if cv < 3.2:
                    cells_str += f" \033[91m{cv:.2f}\033[0m"
                elif cv < 3.4:
                    cells_str += f" \033[93m{cv:.2f}\033[0m"
                else:
                    cells_str += f" {cv:.2f}"
            else:
                cells_str += "    -"

        marker = " <<<" if r["id"] == event["id"] else ""
        print(f"  {t:5.1f}s  {soc:5.1f}%  {v:5.2f}V  {curr:+5.1f}A  {spd:4.1f}  {cells_str}{marker}")

    print(f"\n  Lowest cell: Cell {min_cell_id} at {min_cell_voltage:.3f}V")
    if min_cell_voltage < 3.0:
        print(f"  ⚠ Cell {min_cell_id} hit BMS cutoff voltage — this caused the shutdown")
    elif min_cell_voltage < 3.2:
        print(f"  ⚠ Cell {min_cell_id} was dangerously low — likely triggered protection soon after")

    # Show cell ranking at the moment of drop
    drop_row = dict(conn.execute("SELECT * FROM telemetry WHERE id = ?", (event["id"],)).fetchone())
    print(f"\n  Cell ranking at drop moment:")
    cell_voltages = []
    for i in range(1, 15):
        cv = drop_row.get(f"cell_{i}")
        if cv and cv > 0:
            cell_voltages.append((i, cv))
    cell_voltages.sort(key=lambda x: x[1])
    for i, (cell_id, cv) in enumerate(cell_voltages):
        flag = " ← WEAKEST" if i == 0 else (" ← STRONGEST" if i == len(cell_voltages) - 1 else "")
        print(f"    Cell {cell_id:2d}: {cv:.3f}V{flag}")

print(f"\n{'='*70}")
print("\nTo capture the next drop: keep the collector running during a ride")
print("that drains below 20%. The collector logs every 0.5s below 30% SOC.")
