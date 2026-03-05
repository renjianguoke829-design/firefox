import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


class HotTopicsCollector:
    def __init__(self) -> None:
        self.proxy_enabled = os.getenv("PROXY_ENABLED", "false").strip().lower() == "true"
        self.proxies = self._build_proxy_pool()
        self.error_log_path = Path("scripts/error_logs/hot_topics_collector.log")
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)

    def _build_proxy_pool(self) -> list[dict[str, str] | None]:
        if not self.proxy_enabled:
            return [None]

        proxy_pool: list[dict[str, str]] = []
        http_proxy = os.getenv("PROXY_HTTP", "").strip()
        socks5_proxy = os.getenv("PROXY_SOCKS5", "").strip()

        if http_proxy:
            proxy_pool.append({"http": http_proxy, "https": http_proxy})
        if socks5_proxy:
            proxy_pool.append({"http": socks5_proxy, "https": socks5_proxy})

        return proxy_pool or [None]

    def _log_error(self, message: str, extra: dict[str, Any] | None = None) -> None:
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "extra": extra or {},
        }
        with self.error_log_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _request_with_proxy_retry(self, url: str, timeout: float = 15.0) -> requests.Response:
        attempts = 3
        for attempt in range(attempts):
            proxy = self.proxies[attempt % len(self.proxies)]
            try:
                response = requests.get(url, timeout=timeout, proxies=proxy)
                response.raise_for_status()
                return response
            except Exception as exc:
                self._log_error(
                    "request_failed",
                    {
                        "url": url,
                        "attempt": attempt + 1,
                        "proxy": proxy,
                        "error": str(exc),
                    },
                )
                time.sleep(1)
        raise RuntimeError(f"all proxy retries failed for {url}")

    def collect(self, sources: list[str]) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        for source in sources:
            try:
                response = self._request_with_proxy_retry(source)
                collected.append(
                    {
                        "source": source,
                        "collected_at": datetime.utcnow().isoformat(),
                        "content": response.text,
                    }
                )
            except Exception as exc:
                self._log_error("collect_source_failed", {"source": source, "error": str(exc)})
        return collected


if __name__ == "__main__":
    default_sources = [
        "https://r.jina.ai/http://weibo.com",
        "https://r.jina.ai/http://www.zhihu.com/hot",
    ]
    collector = HotTopicsCollector()
    results = collector.collect(default_sources)
    print(json.dumps(results, ensure_ascii=False)[:1000])
