import json
import os
import uuid
from datetime import datetime
from typing import Any

import asyncpg

from .llm_manager import LLMManager


class MarxistAnalyzer:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is not set")

    async def analyze(self, text: str, model: str = "claude") -> dict[str, Any]:
        manager = LLMManager(model_name=model)
        system_prompt = (
            "你是一个严格按照结构化格式输出的分析器。"
            "必须使用以下四个问题框架完成分析：\n"
            "问题一：这件事涉及哪些阶级主体？各自的物质利益是什么？\n"
            "问题二：表面现象背后的生产关系矛盾是什么？\n"
            "问题三：国家机器在这个矛盾中处于什么位置？服务于谁？\n"
            "问题四：这个矛盾的历史走向是什么？会如何激化或转化？\n"
            "输出必须是JSON对象，包含字段：facts, subjects, contradiction, state_apparatus, observable_signals, trajectory。"
        )
        raw = await manager.generate(text, system_prompt=system_prompt)
        parsed = self._parse_json(raw)
        await self._save_card(text, parsed)
        return parsed

    def _parse_json(self, raw: str) -> dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        data = json.loads(cleaned)
        required = ["facts", "subjects", "contradiction", "state_apparatus", "observable_signals", "trajectory"]
        for key in required:
            data.setdefault(key, "")
        return data

    async def _save_card(self, source_text: str, data: dict[str, Any]) -> None:
        conn = await asyncpg.connect(self.database_url)
        try:
            await conn.execute(
                """
                INSERT INTO contradiction_cards(
                    id, title, facts, subjects, contradiction, state_apparatus,
                    observable_signals, trajectory, quality_score, created_at, pipeline_id
                ) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                """,
                uuid.uuid4(),
                source_text[:120],
                data.get("facts", ""),
                data.get("subjects", ""),
                data.get("contradiction", ""),
                data.get("state_apparatus", ""),
                data.get("observable_signals", ""),
                data.get("trajectory", ""),
                data.get("quality_score", 7),
                datetime.utcnow(),
                None,
            )
        finally:
            await conn.close()
