import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import asyncpg

from rabbit.rabbit_sdk.kernel_bridge import KernelBridge


class PipelineOrchestrator:
    def __init__(self, config_path: str = "pipeline/config.json") -> None:
        self.config_path = Path(config_path)
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is not set")
        self.kernel_bridge = KernelBridge()
        self._config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"pipeline config not found: {self.config_path}")
        with self.config_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    async def run_pipeline(
        self,
        pipeline_name: str,
        initial_input: str,
        require_confirm: Callable[[dict[str, Any]], bool] | None = None,
    ) -> list[dict[str, Any]]:
        await self.kernel_bridge.connect()
        pipeline = self._get_pipeline(pipeline_name)
        stage_outputs: list[dict[str, Any]] = []
        stage_input = initial_input

        for index, stage in enumerate(pipeline.get("stages", []), start=1):
            started = time.perf_counter()
            stage_name = stage.get("name", f"stage-{index}")
            command_payload = {
                "pipeline": pipeline_name,
                "stage_index": index,
                "stage_name": stage_name,
                "input": stage_input,
            }
            command_result = await self.kernel_bridge.send_command("start_stage", command_payload)
            output_result = await self.kernel_bridge.wait_output(
                conversation_id=f"{pipeline_name}:{index}",
                timeout=120,
            )
            duration_ms = int((time.perf_counter() - started) * 1000)

            stage_record = {
                "index": index,
                "stage": stage_name,
                "command_result": command_result,
                "output_result": output_result,
            }
            stage_outputs.append(stage_record)

            await self._write_pipeline_log(
                pipeline_name=pipeline_name,
                stage=stage_name,
                ai_model=str(stage.get("ai_model", "kernel")),
                project_name=str(stage.get("project_name", pipeline_name)),
                input_text=stage_input,
                output_text=json.dumps(output_result, ensure_ascii=False),
                duration_ms=duration_ms,
                quality_score=int(stage.get("quality_score", 0)),
            )

            if require_confirm is not None:
                approved = require_confirm(stage_record)
                if not approved:
                    break

            stage_input = output_result.get("output", stage_input)

        return stage_outputs

    def _get_pipeline(self, pipeline_name: str) -> dict[str, Any]:
        pipelines = self._config.get("pipelines", [])
        for pipeline in pipelines:
            if pipeline.get("name") == pipeline_name:
                return pipeline
        raise ValueError(f"pipeline not found: {pipeline_name}")

    async def _write_pipeline_log(
        self,
        pipeline_name: str,
        stage: str,
        ai_model: str,
        project_name: str,
        input_text: str,
        output_text: str,
        duration_ms: int,
        quality_score: int,
    ) -> None:
        conn = await asyncpg.connect(self.database_url)
        try:
            await conn.execute(
                """
                INSERT INTO pipeline_logs(
                    id, pipeline_name, stage, ai_model, project_name,
                    input, output, duration_ms, quality_score, created_at
                ) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                """,
                uuid.uuid4(),
                pipeline_name,
                stage,
                ai_model,
                project_name,
                input_text,
                output_text,
                duration_ms,
                quality_score,
                datetime.utcnow(),
            )
        finally:
            await conn.close()


async def run_with_terminal_confirmation(pipeline_name: str, initial_input: str) -> list[dict[str, Any]]:
    orchestrator = PipelineOrchestrator()

    def _confirm(stage_record: dict[str, Any]) -> bool:
        stage_title = f"[{stage_record['index']}] {stage_record['stage']}"
        print(f"Stage completed: {stage_title}")
        answer = input("Confirm next stage? (yes/no): ").strip().lower()
        return answer in {"y", "yes"}

    return await orchestrator.run_pipeline(
        pipeline_name=pipeline_name,
        initial_input=initial_input,
        require_confirm=_confirm,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        raise SystemExit("Usage: python pipeline/orchestrator.py <pipeline_name> <input>")

    asyncio.run(run_with_terminal_confirmation(sys.argv[1], sys.argv[2]))
