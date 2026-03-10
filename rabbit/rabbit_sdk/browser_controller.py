import json
import socket
from typing import Any


class BrowserController:
    def __init__(self, host: str = "127.0.0.1", port: int = 9998, timeout: float = 30.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def _send(self, payload: dict[str, Any]) -> dict[str, Any]:
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
            data = sock.recv(1024 * 1024)
        if not data:
            return {"ok": False, "error": "empty response"}
        try:
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            return {"ok": False, "error": data.decode("utf-8", errors="replace")}

    def send_command(self, command: str, **kwargs: Any) -> dict[str, Any]:
        payload = {"command": command, **kwargs}
        return self._send(payload)

    def inject_prompt(self, platform: str, prompt: str, project_mode: str = "marxist") -> dict[str, Any]:
        return self.send_command(
            "inject_prompt",
            platform=platform,
            prompt=prompt,
            project_mode=project_mode,
        )
