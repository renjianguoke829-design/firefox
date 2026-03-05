from typing import Any

from .common import load_proxy_config, normalize_item, request_json_with_proxy


INTERNATIONAL_ENDPOINTS = {
    "reddit": "https://www.reddit.com/r/worldnews/hot.json?limit=50",
    "twitter": "https://api.x.com/2/trends/place.json?id=1",
    "hackernews": "https://hacker-news.firebaseio.com/v0/topstories.json",
    "telegram": "https://example-aggregator.local/api/telegram/public",
    "mastodon": "https://mastodon.social/api/v1/timelines/public?limit=50",
    "youtube": "https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&maxResults=50",
    "instagram": "https://example-aggregator.local/api/instagram/hot",
    "facebook": "https://graph.facebook.com/v20.0/me/feed",
    "linkedin": "https://api.linkedin.com/v2/trendingContent",
    "bluesky": "https://public.api.bsky.app/xrpc/app.bsky.feed.getTimeline?limit=50",
    "discord": "https://example-aggregator.local/api/discord/public",
    "substack": "https://example-aggregator.local/api/substack/hot",
}


def _extract_top50(source: str, payload: Any) -> list[dict[str, Any]]:
    if source == "hackernews" and isinstance(payload, list):
        return [
            normalize_item(source, f"hn_story_{story_id}", f"https://news.ycombinator.com/item?id={story_id}", i + 1, 2, 30)
            for i, story_id in enumerate(payload[:50])
        ]

    raw_items: list[Any] = []
    if isinstance(payload, list):
        raw_items = payload
    elif isinstance(payload, dict):
        for key in ("data", "items", "statuses", "posts", "children"):
            value = payload.get(key)
            if isinstance(value, list):
                raw_items = value
                break

    rows: list[dict[str, Any]] = []
    for item in raw_items[:50]:
        body = item.get("data", item) if isinstance(item, dict) else {}
        if not isinstance(body, dict):
            continue
        title = str(body.get("title") or body.get("name") or body.get("text") or body.get("content") or "")
        link = str(body.get("url") or body.get("permalink") or body.get("link") or "")
        heat = body.get("score") or body.get("hot") or body.get("likes") or body.get("upvotes")
        if title:
            rows.append(normalize_item(source, title, link, heat, data_tier=2, destroy_days=30))
    return rows


def collect_international_social() -> list[dict[str, Any]]:
    cfg = load_proxy_config()
    out: list[dict[str, Any]] = []
    for source, endpoint in INTERNATIONAL_ENDPOINTS.items():
        payload = request_json_with_proxy(endpoint, cfg)
        out.extend(_extract_top50(source, payload))
    return out
