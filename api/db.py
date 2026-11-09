import os
from pathlib import Path
from typing import Any

import aiosqlite

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("DB_PATH") or str(ROOT / "olamate.db")


def db_exists() -> bool:
    return Path(DB_PATH).is_file()


def _connect() -> aiosqlite.Connection:
    uri = f"file:{Path(DB_PATH).resolve()}?mode=ro"
    return aiosqlite.connect(uri, uri=True, timeout=5.0)


async def fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    if not db_exists():
        return []
    async with _connect() as conn:
        conn.row_factory = aiosqlite.Row
        try:
            async with conn.execute(sql, params) as cur:
                return [dict(r) for r in await cur.fetchall()]
        except aiosqlite.OperationalError as e:
            if "no such table" in str(e):
                return []
            raise


async def fetch_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = await fetch_all(sql, params)
    return rows[0] if rows else None
