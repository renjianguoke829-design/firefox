import asyncio
import json
from typing import Any


class KernelBridge:
    def __init__(
        self,
        host: str = "127.0.0.1",
        control_port: int = 9997,
        inject_port: int = 9998,
        collect_port: int = 9999,
        timeout: float = 30.0,
    ) -> None:
        self.host = host
        self.control_port = control_port
        self.inject_port = inject_port
        self.collect_port = collect_port
        self.timeout = timeout
        self._collected: list[dict[str, Any]] = []

    async def connect(self) -> bool:
        await self.heartbeat()
        return True

    async def _send_line(self, port: int, payload: dict[str, Any], wait_response: bool = True) -> dict[str, Any]:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, port),
            timeout=self.timeout,
        )
        try:
            writer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
            await writer.drain()
            if not wait_response:
                return {"ok": True}
            raw = await asyncio.wait_for(reader.readline(), timeout=self.timeout)
            if not raw:
                return {"ok": False, "error": "empty response"}
            try:
                return json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                return {"ok": False, "error": raw.decode("utf-8", errors="replace")}
        finally:
            writer.close()
            await writer.wait_closed()

    async def send_command(self, command: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = {"command": command, **(payload or {})}
        return await self._send_line(self.control_port, body)

    async def inject_command(self, platform: str, prompt: str, project_mode: str = "marxist") -> dict[str, Any]:
        return await self._send_line(
            self.inject_port,
            {
                "command": "inject_prompt",
                "platform": platform,
                "prompt": prompt,
                "project_mode": project_mode,
            },
        )

    async def wait_output(self, conversation_id: str | None = None, timeout: float = 60.0) -> dict[str, Any]:
        payload: dict[str, Any] = {"command": "wait_output"}
        if conversation_id:
            payload["conversation_id"] = conversation_id
        result = await self._send_line(self.collect_port, payload)
        if result.get("ok"):
            self._collected.append(result)
        return result

    async def get_collected_data(self) -> list[dict[str, Any]]:
        result = await self._send_line(self.collect_port, {"command": "get_collected_data"})
        if isinstance(result.get("data"), list):
            return result["data"]
        return list(self._collected)

    async def heartbeat(self) -> dict[str, Any]:
        control = await self._send_line(self.control_port, {"command": "heartbeat"})
        inject = await self._send_line(self.inject_port, {"command": "heartbeat"})
        collect = await self._send_line(self.collect_port, {"command": "heartbeat"})
        return {
            "ok": bool(control.get("ok") and inject.get("ok") and collect.get("ok")),
            "control": control,
            "inject": inject,
            "collect": collect,
        }
