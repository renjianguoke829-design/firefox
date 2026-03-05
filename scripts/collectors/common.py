import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests


@dataclass
class CollectorConfig:
    proxy_enabled: bool
    proxies: list[dict[str, str] | None]


def load_proxy_config() -> CollectorConfig:
    enabled = os.getenv("PROXY_ENABLED", "false").strip().lower() == "true"
    if not enabled:
        return CollectorConfig(proxy_enabled=False, proxies=[None])

    pool: list[dict[str, str]] = []
    http_proxy = os.getenv("PROXY_HTTP", "").strip()
    socks5_proxy = os.getenv("PROXY_SOCKS5", "").strip()
    if http_proxy:
        pool.append({"http": http_proxy, "https": http_proxy})
    if socks5_proxy:
        pool.append({"http": socks5_proxy, "https": socks5_proxy})
    return CollectorConfig(proxy_enabled=True, proxies=pool or [None])


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def auto_destroy(days: int | None) -> str | None:
    if days is None:
        return None
    return to_iso(now_utc() + timedelta(days=days))


def normalize_item(source: str, title: str, link: str, heat: Any, data_tier: int, destroy_days: int | None) -> dict[str, Any]:
    collected_at = now_utc()
    return {
        "source": source,
        "title": title,
        "link": link,
        "heat": str(heat) if heat is not None else "",
        "collected_at": to_iso(collected_at),
        "data_tier": data_tier,
        "auto_destroy_at": auto_destroy(destroy_days),
    }


def request_json_with_proxy(url: str, config: CollectorConfig, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float = 20.0, retries: int = 3) -> Any:
    last_error: Exception | None = None
    for i in range(retries):
        proxy = config.proxies[i % len(config.proxies)]
        try:
            response = requests.get(url, params=params, headers=headers, proxies=proxy, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"request failed for {url}: {last_error}")


def write_json_file(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def request_text_with_proxy(url: str, config: CollectorConfig, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float = 20.0, retries: int = 3) -> str:
    last_error: Exception | None = None
    for i in range(retries):
        proxy = config.proxies[i % len(config.proxies)]
        try:
            response = requests.get(url, params=params, headers=headers, proxies=proxy, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"request failed for {url}: {last_error}")
