"""Reddit top.json 抓取器（无需 OAuth 的公开端点）。"""

from datetime import datetime, timezone

import httpx

MIN_SCORE = 50


def parse_listing(data: dict) -> list:
    from app.fetchers import RawItem

    items = []
    for child in data.get("data", {}).get("children", []):
        d = child.get("data", {})
        score = d.get("score") or 0
        if score < MIN_SCORE:
            continue
        title = (d.get("title") or "").strip()
        permalink = d.get("permalink") or ""
        if not title or not permalink:
            continue
        created = d.get("created_utc")
        items.append(
            RawItem(
                title=title,
                url=f"https://www.reddit.com{permalink}",
                author=d.get("author") or "",
                published_at=datetime.fromtimestamp(created, tz=timezone.utc) if created else None,
                content=(d.get("selftext") or "")[:3000],
                extra={"score": score, "external_url": d.get("url") or "", "subreddit": d.get("subreddit") or ""},
            )
        )
    return items


def fetch_reddit(source) -> list:
    from app.fetchers import HTTP_TIMEOUT, USER_AGENT

    r = httpx.get(
        source.url,
        headers={"User-Agent": USER_AGENT},
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
    )
    r.raise_for_status()
    return parse_listing(r.json())
