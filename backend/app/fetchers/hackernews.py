"""Hacker News via Algolia API：AI 关键词、≥100 分、近 36h。"""

import time
from datetime import datetime, timezone

import httpx

KEYWORDS = [
    "AI", "LLM", "GPT", "Claude", "Gemini", "agent", "open source model",
    "MCP", "agent skill", "Claude skill",  # 社区 skill/工具生态跟踪
]
MIN_POINTS = 100
LOOKBACK_SECONDS = 36 * 3600


def parse_response(data: dict) -> list:
    from app.fetchers import RawItem

    items = []
    for hit in data.get("hits", []):
        points = hit.get("points") or 0
        if points < MIN_POINTS:
            continue
        title = (hit.get("title") or "").strip()
        if not title:
            continue
        hn_url = f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        url = hit.get("url") or hn_url
        created = hit.get("created_at_i")
        items.append(
            RawItem(
                title=title,
                url=url,
                author=hit.get("author") or "",
                published_at=datetime.fromtimestamp(created, tz=timezone.utc) if created else None,
                content=(hit.get("story_text") or "")[:3000],
                extra={"points": points, "comments_url": hn_url, "num_comments": hit.get("num_comments", 0)},
            )
        )
    return items


def fetch_hackernews(source) -> list:
    from app.fetchers import HTTP_TIMEOUT, USER_AGENT

    since = int(time.time()) - LOOKBACK_SECONDS
    seen_urls: set[str] = set()
    merged = []
    for kw in KEYWORDS:
        r = httpx.get(
            "https://hn.algolia.com/api/v1/search_by_date",
            params={
                "query": kw,
                "tags": "story",
                "numericFilters": f"points>{MIN_POINTS},created_at_i>{since}",
                "hitsPerPage": 30,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        for item in parse_response(r.json()):
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                merged.append(item)
    return merged
