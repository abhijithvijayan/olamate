import pytest


async def test_health_reports_db(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["db_exists"] is True


async def test_status_returns_latest_row(client):
    r = await client.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert body["soc"] is not None
    assert "collector_running" in body
    assert body["age_seconds"] >= 0


async def test_status_404_when_empty(empty_client):
    r = await empty_client.get("/api/status")
    assert r.status_code == 404


async def test_telemetry_range_and_limit(client):
    status = (await client.get("/api/status")).json()
    to_ts = status["timestamp"]
    r = await client.get("/api/telemetry", params={"from": to_ts - 30, "to": to_ts, "limit": 10})
    rows = r.json()
    assert 1 <= len(rows) <= 10
    assert rows == sorted(rows, key=lambda x: x["timestamp"])
    assert all(to_ts - 30 <= x["timestamp"] <= to_ts for x in rows)


async def test_sessions_list_filters_by_type(client):
    rides = (await client.get("/api/sessions", params={"type": "ride", "limit": 5})).json()
    charges = (await client.get("/api/sessions", params={"type": "charge"})).json()
    assert rides and all(s["type"] == "ride" for s in rides)
    assert charges and all(s["type"] == "charge" for s in charges)
    first = rides[0]
    for key in ("duration_s", "distance_m", "soc_delta", "avg_speed", "max_speed", "in_progress"):
        assert key in first
    assert first["duration_s"] > 0
    assert first["soc_delta"] < 0
    assert charges[0]["soc_delta"] > 0


async def test_sessions_list_rejects_bad_type(client):
    r = await client.get("/api/sessions", params={"type": "flight"})
    assert r.status_code == 422


async def test_session_detail_downsamples(client):
    rides = (await client.get("/api/sessions", params={"type": "ride", "limit": 1})).json()
    sid = rides[0]["id"]
    r = await client.get(f"/api/sessions/{sid}", params={"points": 50})
    body = r.json()
    assert body["session"]["id"] == sid
    assert 0 < len(body["telemetry"]) <= 50
    assert "speed" in body["telemetry"][0]


async def test_session_detail_404(client):
    r = await client.get("/api/sessions/999999")
    assert r.status_code == 404


async def test_battery_health_trend(client):
    body = (await client.get("/api/battery/health")).json()
    assert body["source"] == "snapshots"
    assert body["latest"]["soh"] is not None
    assert len(body["latest"]["cells"]) == 14
    assert 1 <= len(body["trend"]) <= 30
    ts = [t["timestamp"] for t in body["trend"]]
    assert ts == sorted(ts)


async def test_battery_health_empty(empty_client):
    body = (await empty_client.get("/api/battery/health")).json()
    assert body["latest"] is None
    assert body["trend"] == []


async def test_battery_cells(client):
    body = (await client.get("/api/battery/cells")).json()
    assert len(body["cells"]) == 14
    assert body["spread_mV"] >= 0
    assert {c["state"] for c in body["cells"]} <= {"ok", "high", "low", "missing"}


async def test_stats(client):
    body = (await client.get("/api/stats")).json()
    assert body["total_rides"] > 0
    assert body["total_charges"] > 0
    assert body["total_distance_m"] > 0
    assert body["avg_efficiency_wh_per_km"] is not None
    assert body["odometer_m"] is not None


async def test_stats_empty(empty_client):
    body = (await empty_client.get("/api/stats")).json()
    assert body["total_rides"] == 0
    assert body["telemetry_rows"] == 0


@pytest.mark.parametrize("path", ["/api/sessions", "/api/telemetry"])
async def test_lists_empty_when_no_db(empty_client, path):
    r = await empty_client.get(path)
    assert r.status_code == 200
    assert r.json() == []
