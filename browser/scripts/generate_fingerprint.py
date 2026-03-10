import argparse
import json
import random
import uuid
from pathlib import Path

DEVICE_LIBRARY = {
    "generic": {
        "platform": ["Linux x86_64", "Win32"],
        "user_agents": [
            "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
        ],
        "language": ["zh-CN", "en-US"],
        "hardware_concurrency": [4, 8, 12],
        "device_memory": [4, 8, 16],
        "screen": [(1920, 1080, 24), (2560, 1440, 24)],
        "timezone": ["Asia/Shanghai", "UTC"],
        "webgl": [("ANGLE", "Google Inc."), ("Mesa Intel(R) UHD Graphics", "Intel")],
        "fonts": [["Arial", "Segoe UI", "Roboto"], ["Noto Sans", "PingFang SC", "Helvetica"]],
    },
    "macbook_m2_us": {
        "platform": ["MacIntel"],
        "user_agents": ["Mozilla/5.0 (Macintosh; Intel Mac OS X 13.6; rv:128.0) Gecko/20100101 Firefox/128.0"],
        "language": ["en-US"],
        "hardware_concurrency": [8],
        "device_memory": [16],
        "screen": [(2560, 1664, 24)],
        "timezone": ["America/Los_Angeles", "America/New_York"],
        "webgl": [("Apple M2", "Apple")],
        "fonts": [["San Francisco", "Helvetica Neue", "Arial"]],
    },
    "windows11_us": {
        "platform": ["Win32"],
        "user_agents": ["Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"],
        "language": ["en-US"],
        "hardware_concurrency": [8, 16],
        "device_memory": [8, 16],
        "screen": [(1920, 1080, 24), (2560, 1440, 24)],
        "timezone": ["America/Chicago", "America/New_York"],
        "webgl": [("NVIDIA GeForce RTX 3060", "NVIDIA Corporation")],
        "fonts": [["Segoe UI", "Arial", "Calibri", "Times New Roman"]],
    },
    "iphone15_uk": {
        "platform": ["iPhone"],
        "user_agents": ["Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X; rv:128.0) Gecko/20100101 Firefox/128.0"],
        "language": ["en-GB"],
        "hardware_concurrency": [6],
        "device_memory": [6],
        "screen": [(1179, 2556, 24)],
        "timezone": ["Europe/London"],
        "webgl": [("Apple GPU", "Apple")],
        "fonts": [["SF Pro Text", "Helvetica", "Arial"]],
    },
}


def choose(device: str) -> dict:
    base = DEVICE_LIBRARY[device]
    width, height, depth = random.choice(base["screen"])
    renderer, vendor = random.choice(base["webgl"])
    return {
        "profile_id": str(uuid.uuid4()),
        "navigator.platform": random.choice(base["platform"]),
        "navigator.userAgent": random.choice(base["user_agents"]),
        "navigator.language": random.choice(base["language"]),
        "navigator.hardwareConcurrency": random.choice(base["hardware_concurrency"]),
        "navigator.deviceMemory": random.choice(base["device_memory"]),
        "screen.width": width,
        "screen.height": height,
        "screen.colorDepth": depth,
        "timezone": random.choice(base["timezone"]),
        "canvas.noiseSeed": random.randint(10_000_000, 99_999_999),
        "webgl.renderer": renderer,
        "webgl.vendor": vendor,
        "fonts": random.choice(base["fonts"]),
        "battery.random": round(random.uniform(0.15, 0.98), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--device", required=True, choices=sorted(DEVICE_LIBRARY.keys()))
    args = parser.parse_args()

    profile_data = choose(args.device)
    out_dir = Path("browser/profiles")
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{args.profile}.json"
    output_path.write_text(json.dumps(profile_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
