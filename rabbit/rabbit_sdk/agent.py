import asyncio
import os
import time
import uuid
from datetime import datetime
from typing import Any

import asyncpg

from .kernel_bridge import KernelBridge


class Agent:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is not set")
        self.kernel_bridge = KernelBridge()

    async def parallel_analyze(self, text: str, models: list[str] | None = None) -> dict[str, Any]:
        active_models = models or ["claude", "grok", "gemini", "deepseek"]
        await self.kernel_bridge.connect()

        inject_tasks = [
            asyncio.wait_for(
                self.kernel_bridge.inject_command(platform=model_name, prompt=text),
                timeout=30,
            )
            for model_name in active_models
        ]
        inject_results = await asyncio.gather(*inject_tasks, return_exceptions=True)

        output_tasks = [
            asyncio.wait_for(self._collect_model_output(model_name, text), timeout=30)
            for model_name in active_models
        ]
        outputs = await asyncio.gather(*output_tasks, return_exceptions=True)

        merged: dict[str, Any] = {}
        for model_name, inject_result, output_result in zip(active_models, inject_results, outputs):
            if isinstance(inject_result, Exception):
                merged[model_name] = {"error": f"inject failed: {inject_result}"}
                continue
            if isinstance(output_result, Exception):
                merged[model_name] = {"error": str(output_result)}
            else:
                merged[model_name] = output_result
        return merged

    async def _collect_model_output(self, model_name: str, prompt: str) -> dict[str, Any]:
        started = time.perf_counter()
        status = "success"
        output_text = ""
        try:
            result = await self.kernel_bridge.wait_output(conversation_id=model_name, timeout=30)
            if not result.get("ok"):
                status = "error"
                output_text = result.get("error", "wait_output failed")
                return {"error": output_text}
            output_text = result.get("output", "")
            return result
        except Exception as exc:
            status = "error"
            output_text = str(exc)
            raise
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            await self._store_agent_run(model_name, prompt, output_text, duration_ms, status)

    async def _store_agent_run(
        self, model_name: str, prompt: str, output: str, duration_ms: int, status: str
    ) -> None:
        conn = await asyncpg.connect(self.database_url)
        try:
            await conn.execute(
                """
                INSERT INTO agent_runs(id, task, model, prompt, output, duration_ms, token_count, created_at)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8)
                """,
                uuid.uuid4(),
                status,
                model_name,
                prompt,
                output,
                duration_ms,
                0,
                datetime.utcnow(),
            )
        finally:
            await conn.close()
