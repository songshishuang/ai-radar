"""HuggingFace Daily Papers + Trending Models（公开 API）。"""

from datetime import datetime

import httpx


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_papers(data: list) -> list:
    from app.fetchers import RawItem

    items = []
    for entry in data:
        paper = entry.get("paper") or {}
        pid = paper.get("id") or ""
        title = (paper.get("title") or "").strip().replace("\n", " ")
        if not pid or not title:
            continue
        items.append(
            RawItem(
                title=title,
                url=f"https://huggingface.co/papers/{pid}",
                published_at=_parse_dt(entry.get("publishedAt") or paper.get("publishedAt")),
                content=(paper.get("summary") or "")[:3000],
                extra={"upvotes": paper.get("upvotes", 0)},
            )
        )
    return items


def parse_models(data: list) -> list:
    from app.fetchers import RawItem

    items = []
    for m in data:
        mid = m.get("id") or m.get("modelId") or ""
        if not mid:
            continue
        tags = m.get("tags") or []
        pipeline = m.get("pipeline_tag") or ""
        items.append(
            RawItem(
                title=f"HF Trending Model: {mid}",
                url=f"https://huggingface.co/{mid}",
                published_at=_parse_dt(m.get("createdAt")),
                content=f"pipeline: {pipeline}; downloads: {m.get('downloads', 0)}; likes: {m.get('likes', 0)}; tags: {', '.join(tags[:10])}",
                extra={"likes": m.get("likes", 0), "downloads": m.get("downloads", 0)},
            )
        )
    return items


def fetch_hf_papers(source) -> list:
    from app.fetchers import HTTP_TIMEOUT, USER_AGENT

    r = httpx.get(
        "https://huggingface.co/api/daily_papers",
        params={"limit": 20},
        headers={"User-Agent": USER_AGENT},
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return parse_papers(r.json())


def fetch_hf_models(source) -> list:
    from app.fetchers import HTTP_TIMEOUT, USER_AGENT

    r = httpx.get(
        "https://huggingface.co/api/models",
        params={"sort": "trendingScore", "direction": -1, "limit": 15},
        headers={"User-Agent": USER_AGENT},
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return parse_models(r.json())


def parse_spaces(data: list) -> list:
    """HF Spaces trending（热门 AI 应用 demo）。"""
    from app.fetchers import RawItem

    items = []
    for s in data:
        sid = s.get("id") or ""
        if not sid:
            continue
        sdk = s.get("sdk") or ""
        items.append(
            RawItem(
                title=f"HF Space: {sid}",
                url=f"https://huggingface.co/spaces/{sid}",
                published_at=_parse_dt(s.get("createdAt")),
                content=f"AI 应用 demo（sdk: {sdk}）; likes: {s.get('likes', 0)}",
                extra={"likes": s.get("likes", 0), "sdk": sdk},
            )
        )
    return items


def fetch_hf_spaces(source) -> list:
    from app.fetchers import HTTP_TIMEOUT, USER_AGENT

    r = httpx.get(
        "https://huggingface.co/api/spaces",
        params={"sort": "trendingScore", "direction": -1, "limit": 15},
        headers={"User-Agent": USER_AGENT},
        timeout=HTTP_TIMEOUT,
    )
    r.raise_for_status()
    return parse_spaces(r.json())
