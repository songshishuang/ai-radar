"""通用 RSS/Atom 抓取器。"""

import time
from datetime import datetime, timezone

import feedparser
import httpx
from bs4 import BeautifulSoup


def _clean_html(html: str, limit: int = 3000) -> str:
    if not html:
        return ""
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    return text[:limit]


def _entry_time(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        t = entry.get(attr)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return None


def parse_feed(text: str, source_url: str = "") -> list:
    from app.fetchers import RawItem

    parsed = feedparser.parse(text)
    items = []
    for e in parsed.entries:
        url = e.get("link") or ""
        title = (e.get("title") or "").strip()
        if not title or not url:
            continue
        content = ""
        if e.get("content"):
            content = e["content"][0].get("value", "")
        elif e.get("summary"):
            content = e["summary"]
        items.append(
            RawItem(
                title=title,
                url=url,
                author=(e.get("author") or "").strip(),
                published_at=_entry_time(e),
                content=_clean_html(content),
            )
        )
    return items


def fetch_rss(source) -> list:
    from app.fetchers import HTTP_TIMEOUT, USER_AGENT

    r = httpx.get(
        source.url,
        headers={"User-Agent": USER_AGENT},
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
    )
    r.raise_for_status()
    return parse_feed(r.text, source_url=source.url)
