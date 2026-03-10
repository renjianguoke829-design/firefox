import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rabbit.rabbit_sdk.kernel_bridge import KernelBridge


def parse_env_file(path: str = ".env") -> dict[str, str]:
    result: dict[str, str] = {}
    p = Path(path)
    if not p.exists():
        return result
    for line in p.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def parse_csv(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


async def collect_for_platforms(kernel: KernelBridge, firefox_variant: str, platforms: list[str], category: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for platform in platforms:
        login_result = await kernel.send_command(
            "platform_login",
            {
                "variant": firefox_variant,
                "platform": platform,
                "category": category,
            },
        )
        pull_result = await kernel.send_command(
            "pull_platform_content",
            {
                "variant": firefox_variant,
                "platform": platform,
                "category": category,
            },
        )
        rows.append(
            {
                "platform": platform,
                "category": category,
                "variant": firefox_variant,
                "time": datetime.now(timezone.utc).isoformat(),
                "login": login_result,
                "pull": pull_result,
            }
        )
    return rows


def write_to_cloud_with_rclone(payload: dict[str, Any], remote_path: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "pre_production.json"
        src.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        subprocess.run(["rclone", "copy", str(src), remote_path], check=True)


async def main() -> None:
    env = parse_env_file()
    domestic = parse_csv(env.get("ENABLED_DOMESTIC", ""))
    international = parse_csv(env.get("ENABLED_INTERNATIONAL", ""))
    ai_platforms = parse_csv(env.get("ENABLED_AI", ""))

    kernel = KernelBridge()
    await kernel.connect()

    domestic_rows = await collect_for_platforms(kernel, "domestic", domestic, "domestic_social")
    international_rows = await collect_for_platforms(kernel, "international", international, "international_social")
    ai_rows = await collect_for_platforms(kernel, "international", ai_platforms, "ai_platform")

    payload = {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "domestic": domestic_rows,
        "international": international_rows,
        "ai": ai_rows,
    }

    target = env.get("RCLONE_DB_PATH", "/mnt/cloud/raw/pre_production/")
    write_to_cloud_with_rclone(payload, target)
    print(json.dumps({"ok": True, "target": target, "counts": {"domestic": len(domestic_rows), "international": len(international_rows), "ai": len(ai_rows)}}, ensure_ascii=False))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
