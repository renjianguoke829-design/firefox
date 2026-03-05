from typing import Any

from .common import load_proxy_config, normalize_item, request_json_with_proxy


DOMESTIC_ENDPOINTS = {
    "weibo": "https://weibo.com/ajax/side/hotSearch",
    "zhihu": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
    "bilibili": "https://api.bilibili.com/x/web-interface/ranking/v2",
    "douyin": "https://example-aggregator.local/api/douyin/hot",
    "xiaohongshu": "https://example-aggregator.local/api/xiaohongshu/hot",
    "wechat": "https://example-aggregator.local/api/wechat/hot",
    "douban": "https://www.douban.com/j/app/radio/channels",
    "hupu": "https://example-aggregator.local/api/hupu/hot",
    "baidu": "https://top.baidu.com/api/board",
    "toutiao": "https://example-aggregator.local/api/toutiao/hot",
}


def _extract_top50(source: str, payload: Any) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if isinstance(payload, list):
        raw_items = payload
    elif isinstance(payload, dict):
        raw_items = []
        for key in ("data", "list", "items", "cards"):
            value = payload.get(key)
            if isinstance(value, list):
                raw_items = value
                break
    else:
        raw_items = []

    for item in raw_items[:50]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("word") or item.get("name") or "")
        link = str(item.get("url") or item.get("link") or item.get("uri") or "")
        heat = item.get("hot") or item.get("heat") or item.get("score") or item.get("hot_value")
        if title:
            candidates.append(normalize_item(source, title, link, heat, data_tier=3, destroy_days=7))
    return candidates


def collect_domestic_social() -> list[dict[str, Any]]:
    cfg = load_proxy_config()
    all_rows: list[dict[str, Any]] = []
    for source, endpoint in DOMESTIC_ENDPOINTS.items():
        payload = request_json_with_proxy(endpoint, cfg)
        all_rows.extend(_extract_top50(source, payload))
    return all_rows
