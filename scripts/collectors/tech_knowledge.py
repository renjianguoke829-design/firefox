import os
import xml.etree.ElementTree as ET
from typing import Any

from .common import (
    load_proxy_config,
    normalize_item,
    request_json_with_proxy,
    request_text_with_proxy,
    write_json_file,
)


HF_DATASET_TAGS = ["chinese", "social", "nlp", "text-classification"]
GITHUB_KEYWORDS = [
    "AI ethics",
    "labor tech",
    "surveillance",
    "platform economy",
    "social movement",
    "marxist",
    "communist",
    "socialist",
]
ARXIV_KEYWORDS = [
    "AI",
    "social movement",
    "labor",
    "surveillance",
    "platform economy",
    "misinformation",
    "censorship",
]


def collect_huggingface() -> list[dict[str, Any]]:
    cfg = load_proxy_config()
    token = os.getenv("HUGGINGFACE_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    datasets = request_json_with_proxy("https://huggingface.co/api/datasets", cfg, headers=headers, params={"limit": 50})
    models = request_json_with_proxy("https://huggingface.co/api/models", cfg, headers=headers, params={"limit": 50, "sort": "downloads"})
    discussions = request_json_with_proxy("https://huggingface.co/api/discussions", cfg, headers=headers, params={"limit": 50})

    rows: list[dict[str, Any]] = []
    raw_dump: dict[str, Any] = {"datasets": datasets, "models": models, "discussions": discussions}

    for item in datasets[:50] if isinstance(datasets, list) else []:
        tags = item.get("tags", []) if isinstance(item, dict) else []
        if not any(tag in HF_DATASET_TAGS for tag in tags):
            continue
        title = item.get("id", "")
        link = f"https://huggingface.co/datasets/{title}" if title else ""
        rows.append(normalize_item("huggingface_dataset", title, link, item.get("downloads", 0), 1, None))

    for item in models[:50] if isinstance(models, list) else []:
        model_id = item.get("id", "") if isinstance(item, dict) else ""
        rows.append(normalize_item("huggingface_model", model_id, f"https://huggingface.co/{model_id}", item.get("downloads", 0), 1, None))

    for item in discussions[:50] if isinstance(discussions, list) else []:
        title = item.get("title", "") if isinstance(item, dict) else ""
        link = item.get("url", "") if isinstance(item, dict) else ""
        rows.append(normalize_item("huggingface_discussion", title, link, item.get("num_comments", 0), 1, None))

    write_json_file("/mnt/cloud/raw/huggingface/metadata.json", raw_dump)
    return rows


def collect_github() -> list[dict[str, Any]]:
    cfg = load_proxy_config()
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    rows: list[dict[str, Any]] = []

    for kw in GITHUB_KEYWORDS:
        repos = request_json_with_proxy(
            "https://api.github.com/search/repositories",
            cfg,
            headers=headers,
            params={"q": kw, "sort": "stars", "order": "desc", "per_page": 10},
        )
        for repo in repos.get("items", [])[:10]:
            title = repo.get("full_name", "")
            link = repo.get("html_url", "")
            rows.append(normalize_item("github_repo", title, link, repo.get("stargazers_count", 0), 1, None))

            readme = request_json_with_proxy(
                f"https://api.github.com/repos/{title}/readme",
                cfg,
                headers={**headers, "Accept": "application/vnd.github.raw+json"},
            )
            rows.append(normalize_item("github_readme", f"README:{title}", link, len(str(readme)), 1, None))

    return rows[:50]


def collect_arxiv() -> list[dict[str, Any]]:
    cfg = load_proxy_config()
    max_results = int(os.getenv("ARXIV_MAX_RESULTS", "50"))
    query = " OR ".join(f"all:{kw}" for kw in ARXIV_KEYWORDS)
    xml_text = request_text_with_proxy(
        "https://export.arxiv.org/api/query",
        cfg,
        params={"search_query": query, "start": 0, "max_results": max_results},
    )

    root = ET.fromstring(xml_text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    rows: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns)[:50]:
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        link = (entry.findtext("atom:id", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
        rows.append(normalize_item("arxiv", title, link, len(summary), 1, None))
    return rows


def collect_tech_knowledge() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    out.extend(collect_huggingface())
    out.extend(collect_github())
    out.extend(collect_arxiv())
    return out
