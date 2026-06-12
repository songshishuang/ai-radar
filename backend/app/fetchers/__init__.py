"""抓取器注册表。每个 fetcher: (Source) -> list[RawItem]，只抓不入库。"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from app.models import Source


@dataclass
class RawItem:
    title: str
    url: str
    author: str = ""
    published_at: datetime | None = None
    content: str = ""
    extra: dict = field(default_factory=dict)


from app.fetchers.github_trending import fetch_github_trending  # noqa: E402
from app.fetchers.hackernews import fetch_hackernews  # noqa: E402
from app.fetchers.huggingface import fetch_hf_models, fetch_hf_papers  # noqa: E402
from app.fetchers.reddit import fetch_reddit  # noqa: E402
from app.fetchers.rss import fetch_rss  # noqa: E402

FETCHERS: dict[str, Callable[[Source], list[RawItem]]] = {
    "rss": fetch_rss,
    "hackernews": fetch_hackernews,
    "github_trending": fetch_github_trending,
    "hf_papers": fetch_hf_papers,
    "hf_models": fetch_hf_models,
    "reddit": fetch_reddit,
    # "rsshub" 故意不注册：本地无 RSSHub 实例，ingest 会将其标记 degraded
}

USER_AGENT = "Mozilla/5.0 (compatible; ai-intel-bot/0.1)"
HTTP_TIMEOUT = 20.0
