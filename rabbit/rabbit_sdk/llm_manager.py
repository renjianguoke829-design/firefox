import asyncio
import json
import os
from typing import Any, Optional
from urllib import request


class LLMManager:
    def __init__(self, model_name: str = "gemini", timeout: int = 30) -> None:
        self.model_name = model_name.lower()
        self.timeout = timeout

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        last_error: Optional[Exception] = None
        for attempt in range(3):
            try:
                return await self._generate_once(prompt, system_prompt)
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(2)
        raise RuntimeError(f"Failed to generate after retries: {last_error}")

    async def _generate_once(self, prompt: str, system_prompt: Optional[str]) -> str:
        if self.model_name == "gemini":
            return await self._call_gemini(prompt, system_prompt)
        if self.model_name == "claude":
            return await self._call_claude(prompt, system_prompt)
        if self.model_name == "grok":
            return await self._call_grok(prompt, system_prompt)
        if self.model_name == "deepseek":
            return await self._call_deepseek(prompt, system_prompt)
        if self.model_name == "ollama":
            return await self._call_ollama(prompt, system_prompt)
        raise ValueError(f"Unsupported model: {self.model_name}")

    async def _post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        def _do_request() -> dict[str, Any]:
            req = request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", **headers},
                method="POST",
            )
            with request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)

        return await asyncio.to_thread(_do_request)

    async def _call_gemini(self, prompt: str, system_prompt: Optional[str]) -> str:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        content = prompt if not system_prompt else f"{system_prompt}\n\n{prompt}"
        data = await self._post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            {"contents": [{"parts": [{"text": content}]}]},
            {},
        )
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_claude(self, prompt: str, system_prompt: Optional[str]) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        data = await self._post_json(
            "https://api.anthropic.com/v1/messages",
            {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4096,
                "system": system_prompt or "",
                "messages": [{"role": "user", "content": prompt}],
            },
            {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        )
        return "".join(item.get("text", "") for item in data.get("content", []))

    async def _call_grok(self, prompt: str, system_prompt: Optional[str]) -> str:
        api_key = os.getenv("GROK_API_KEY")
        if not api_key:
            raise RuntimeError("GROK_API_KEY is not set")
        data = await self._post_json(
            "https://api.x.ai/v1/chat/completions",
            {
                "model": os.getenv("GROK_MODEL", "grok-2-latest"),
                "messages": [
                    *([{"role": "system", "content": system_prompt}] if system_prompt else []),
                    {"role": "user", "content": prompt},
                ],
            },
            {"Authorization": f"Bearer {api_key}"},
        )
        return data["choices"][0]["message"]["content"]

    async def _call_deepseek(self, prompt: str, system_prompt: Optional[str]) -> str:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")
        data = await self._post_json(
            "https://api.deepseek.com/chat/completions",
            {
                "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                "messages": [
                    *([{"role": "system", "content": system_prompt}] if system_prompt else []),
                    {"role": "user", "content": prompt},
                ],
            },
            {"Authorization": f"Bearer {api_key}"},
        )
        return data["choices"][0]["message"]["content"]

    async def _call_ollama(self, prompt: str, system_prompt: Optional[str]) -> str:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "dolphin3-mistral-24b")
        data = await self._post_json(
            f"{base_url}/api/generate",
            {
                "model": model,
                "prompt": prompt,
                "system": system_prompt or "",
                "stream": False,
            },
            {},
        )
        return data["response"]
