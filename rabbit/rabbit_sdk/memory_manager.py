import os
from collections import defaultdict
from typing import Any

import asyncpg


class MemoryManager:
    def __init__(self) -> None:
        self._cache: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise RuntimeError("DATABASE_URL is not set")
            self._pool = await asyncpg.create_pool(database_url)
            await self._init_schema()
        return self._pool

    async def _init_schema(self) -> None:
        pool = self._pool
        if pool is None:
            return
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_history (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_memory_history_session ON memory_history(session_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_memory_history_content ON memory_history USING GIN(to_tsvector('simple', content));
                """
            )

    async def add_memory(self, session_id: str, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        entry = {"session_id": session_id, "role": role, "content": content, "metadata": metadata or {}}
        self._cache[session_id].append(entry)
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO memory_history(session_id, role, content, metadata) VALUES($1, $2, $3, $4::jsonb)",
                session_id,
                role,
                content,
                metadata or {},
            )

    async def get_history(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT session_id, role, content, metadata, created_at
                FROM memory_history
                WHERE session_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                session_id,
                limit,
            )
        return [dict(row) for row in rows]

    async def search_memory(self, keyword: str) -> list[dict[str, Any]]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT session_id, role, content, metadata, created_at
                FROM memory_history
                WHERE to_tsvector('simple', content) @@ plainto_tsquery('simple', $1)
                ORDER BY created_at DESC
                LIMIT 100
                """,
                keyword,
            )
        return [dict(row) for row in rows]
