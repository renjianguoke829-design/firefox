import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable

import asyncpg

from .domestic_social import collect_domestic_social
from .international_social import collect_international_social
from .tech_knowledge import collect_tech_knowledge


LOG_DIR = Path("/mnt/cloud/raw/collector_logs")


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_log(name: str, payload: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{name}.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


async def _run_collector(name: str, interval_seconds: int, func: Callable[[], list[dict]]) -> None:
    while True:
        started = _timestamp()
        try:
            rows = await asyncio.to_thread(func)
            await _write_raw_data(rows)
            _write_log(name, {"time": started, "status": "ok", "count": len(rows)})
        except Exception as exc:
            _write_log(name, {"time": started, "status": "error", "error": str(exc)})
        await asyncio.sleep(interval_seconds)


async def _write_raw_data(rows: list[dict]) -> None:
    if not rows:
        return
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    conn = await asyncpg.connect(database_url)
    try:
        await conn.executemany(
            """
            INSERT INTO raw_data(source, content, collected_at, is_refined, refined_at)
            VALUES($1,$2,$3,$4,$5)
            """,
            [
                (
                    row.get("source", "unknown"),
                    json.dumps(row, ensure_ascii=False),
                    row.get("collected_at"),
                    False,
                    None,
                )
                for row in rows
            ],
        )
    finally:
        await conn.close()


async def main() -> None:
    tasks: list[Awaitable[None]] = [
        _run_collector("domestic_social", 30 * 60, collect_domestic_social),
        _run_collector("international_social", 2 * 60 * 60, collect_international_social),
        _run_collector("tech_knowledge", 6 * 60 * 60, collect_tech_knowledge),
    ]
    await asyncio.gather(*tasks, return_exceptions=False)


if __name__ == "__main__":
    asyncio.run(main())
