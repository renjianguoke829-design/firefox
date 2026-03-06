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


MARXIST_PROMPT = (
    "问题一：这件事涉及哪些阶级主体？各自的物质利益是什么？\n"
    "问题二：表面现象背后的生产关系矛盾是什么？\n"
    "问题三：国家机器在这个矛盾中处于什么位置？服务于谁？\n"
    "问题四：这个矛盾的历史走向是什么？会如何激化或转化？"
)
CONTROL_PROMPT = "请从自由主义与常见反驳角度分析，避免使用马列框架。"


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
        stages = pipeline.get("stages", [])[:5]
        stage_input = initial_input
        outputs: list[dict[str, Any]] = []

        for stage_index, stage in enumerate(stages, start=1):
            stage_name = str(stage.get("name", f"stage-{stage_index}"))
            started = time.perf_counter()
            marxist_task = self._run_version(
                pipeline_name=pipeline_name,
                stage_name=stage_name,
                stage_index=stage_index,
                version="marxist",
                input_text=stage_input,
                system_prompt=MARXIST_PROMPT,
            )
            control_task = self._run_version(
                pipeline_name=pipeline_name,
                stage_name=stage_name,
                stage_index=stage_index,
                version="control",
                input_text=stage_input,
                system_prompt=CONTROL_PROMPT,
            )
            marxist_result, control_result = await asyncio.gather(marxist_task, control_task)
            elapsed = int((time.perf_counter() - started) * 1000)

            stage_record = {
                "stage_index": stage_index,
                "stage_name": stage_name,
                "workstations": 2,
                "results": {
                    "marxist": marxist_result,
                    "control": control_result,
                },
                "duration_ms": elapsed,
            }
            outputs.append(stage_record)

            await self._write_pipeline_log(
                pipeline_name=pipeline_name,
                stage=f"{stage_name}:checkpoint",
                ai_model="dual-runner",
                project_name=pipeline_name,
                input_text=stage_input,
                output_text=json.dumps(stage_record, ensure_ascii=False),
                duration_ms=elapsed,
                quality_score=0,
            )

            if require_confirm is not None:
                if not require_confirm(stage_record):
                    break

            stage_input = marxist_result.get("output") or control_result.get("output") or stage_input

        return outputs

    async def trigger_decision_assistant(self, prompt: str) -> dict[str, Any]:
        await self.kernel_bridge.connect()
        command = await self.kernel_bridge.send_command(
            "decision_assistant",
            {
                "workstation": 11,
                "prompt": prompt,
            },
        )
        output = await self.kernel_bridge.wait_output(conversation_id="decision_assistant", timeout=90)
        merged = {"command": command, "output": output}
        await self._write_pipeline_log(
            pipeline_name="decision_assistant",
            stage="assistant",
            ai_model="decision-assistant",
            project_name="independent",
            input_text=prompt,
            output_text=json.dumps(merged, ensure_ascii=False),
            duration_ms=0,
            quality_score=0,
        )
        return merged

    async def _run_version(
        self,
        pipeline_name: str,
        stage_name: str,
        stage_index: int,
        version: str,
        input_text: str,
        system_prompt: str,
    ) -> dict[str, Any]:
        run_id = f"{pipeline_name}:{stage_index}:{version}"
        started = time.perf_counter()
        command_payload = {
            "pipeline": pipeline_name,
            "stage": stage_name,
            "stage_index": stage_index,
            "version": version,
            "workstation": (stage_index - 1) * 2 + (1 if version == "marxist" else 2),
            "system_prompt": system_prompt,
            "input": input_text,
        }
        command_result = await self.kernel_bridge.send_command("start_stage_version", command_payload)
        output_result = await self.kernel_bridge.wait_output(conversation_id=run_id, timeout=120)
        duration_ms = int((time.perf_counter() - started) * 1000)

        merged = {"command": command_result, **output_result}
        await self._write_pipeline_log(
            pipeline_name=pipeline_name,
            stage=f"{stage_name}:{version}",
            ai_model=f"kernel-{version}",
            project_name=pipeline_name,
            input_text=input_text,
            output_text=json.dumps(merged, ensure_ascii=False),
            duration_ms=duration_ms,
            quality_score=0,
        )
        return merged

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
        print(f"Stage finished: {stage_record['stage_name']} ({stage_record['stage_index']}/5)")
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
