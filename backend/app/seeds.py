"""26 个首批数据源种子。seed_sources 幂等（按 name upsert）。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Source

SEED_SOURCES: list[dict] = [
    # ── 核心厂商官方源 ──
    {"category": "vendor", "name": "OpenAI News", "fetch_method": "rss", "url": "https://openai.com/news/rss.xml"},
    # Anthropic 官方无 RSS，用社区维护镜像（Olshansk/rss-feeds）
    {"category": "vendor", "name": "Anthropic News", "fetch_method": "rss", "url": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml"},
    {"category": "vendor", "name": "Google DeepMind", "fetch_method": "rss", "url": "https://deepmind.google/blog/rss.xml"},
    {"category": "vendor", "name": "Google AI Blog", "fetch_method": "rss", "url": "https://blog.google/technology/ai/rss/"},
    {"category": "vendor", "name": "Meta AI Blog", "fetch_method": "rss", "url": "https://ai.meta.com/blog/rss/", "enabled": False},  # 官方已撤 RSS
    {"category": "vendor", "name": "Microsoft AI", "fetch_method": "rss", "url": "https://news.microsoft.com/source/topics/ai/feed/"},
    {"category": "vendor", "name": "HuggingFace Blog", "fetch_method": "rss", "url": "https://huggingface.co/blog/feed.xml"},
    {"category": "vendor", "name": "Mistral News", "fetch_method": "rss", "url": "https://mistral.ai/feed.xml", "enabled": False},  # 官方无 RSS
    # ── 产研 AI 范式 ──
    {"category": "paradigm", "name": "Claude Code Releases", "fetch_method": "rss", "url": "https://github.com/anthropics/claude-code/releases.atom"},
    {"category": "paradigm", "name": "Cursor Changelog", "fetch_method": "rss", "url": "https://www.cursor.com/changelog/rss.xml"},
    {"category": "paradigm", "name": "GitHub Blog", "fetch_method": "rss", "url": "https://github.blog/feed/"},
    {"category": "paradigm", "name": "Vercel Blog", "fetch_method": "rss", "url": "https://vercel.com/atom"},
    {"category": "paradigm", "name": "LangChain Blog", "fetch_method": "rss", "url": "https://blog.langchain.dev/rss/"},
    # ── 社区与开源 ──
    {"category": "community", "name": "Hacker News AI", "fetch_method": "hackernews", "url": "https://hn.algolia.com/api/v1/search_by_date"},
    {"category": "community", "name": "GitHub Trending", "fetch_method": "github_trending", "url": "https://github.com/trending?since=daily"},
    {"category": "community", "name": "HF Daily Papers", "fetch_method": "hf_papers", "url": "https://huggingface.co/api/daily_papers"},
    {"category": "community", "name": "HF Trending Models", "fetch_method": "hf_models", "url": "https://huggingface.co/api/models"},
    # Reddit 屏蔽数据中心/脚本 UA（403），降级禁用；社区热点由 HN 覆盖，VPS 部署可改走 RSSHub
    {"category": "community", "name": "r/LocalLLaMA", "fetch_method": "reddit", "url": "https://www.reddit.com/r/LocalLLaMA/top.json?t=day&limit=25", "enabled": False},
    {"category": "community", "name": "r/MachineLearning", "fetch_method": "reddit", "url": "https://www.reddit.com/r/MachineLearning/top.json?t=day&limit=25", "enabled": False},
    # ── 行业媒体 / Newsletter ──
    {"category": "media", "name": "TechCrunch AI", "fetch_method": "rss", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"category": "media", "name": "The Verge AI", "fetch_method": "rss", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"category": "media", "name": "VentureBeat AI", "fetch_method": "rss", "url": "https://venturebeat.com/category/ai/feed/"},
    {"category": "media", "name": "Ben's Bites", "fetch_method": "rss", "url": "https://bensbites.beehiiv.com/feed", "enabled": False},  # beehiiv feed ID 不公开
    {"category": "media", "name": "Product Hunt", "fetch_method": "rss", "url": "https://www.producthunt.com/feed"},
    # ── Twitter/X（本地无 RSSHub，默认禁用；VPS 部署后启用） ──
    {"category": "twitter", "name": "X: @sama", "fetch_method": "rsshub", "url": "rsshub://twitter/user/sama", "enabled": False},
    {"category": "twitter", "name": "X: @karpathy", "fetch_method": "rsshub", "url": "rsshub://twitter/user/karpathy", "enabled": False},
]


def seed_sources(session: Session) -> int:
    created = 0
    for spec in SEED_SOURCES:
        existing = session.execute(select(Source).where(Source.name == spec["name"])).scalar_one_or_none()
        if existing:
            continue
        session.add(Source(**spec))
        created += 1
    session.commit()
    return created
