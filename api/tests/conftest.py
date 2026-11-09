import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture(scope="session")
def seeded_db(tmp_path_factory) -> str:
    from seed_demo import seed

    path = str(tmp_path_factory.mktemp("db") / "olamate.db")
    seed(path, days=3)
    return path


@pytest.fixture
def client(seeded_db, monkeypatch):
    import db
    from httpx import ASGITransport, AsyncClient

    monkeypatch.setattr(db, "DB_PATH", seeded_db)
    from main import app

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
def empty_client(tmp_path, monkeypatch):
    import db
    from httpx import ASGITransport, AsyncClient

    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "missing.db"))
    from main import app

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
