"""GitHub Trending（daily）页面解析 + AI 关键词过滤。"""

import re

import httpx
from bs4 import BeautifulSoup

AI_PATTERN = re.compile(
    r"\b(ai|llm|gpt|claude|gemini|agent|agents|agentic|rag|diffusion|transformer|"
    r"machine.?learning|deep.?learning|neural|model|mcp|copilot|inference)\b",
    re.IGNORECASE,
)


def parse_trending(html: str) -> list:
    from app.fetchers import RawItem

    soup = BeautifulSoup(html, "html.parser")
    items = []
    for row in soup.select("article.Box-row"):
        a = row.select_one("h2 a")
        if not a or not a.get("href"):
            continue
        repo = a["href"].strip("/")
        desc_el = row.select_one("p")
        desc = desc_el.get_text(strip=True) if desc_el else ""
        stars_el = row.select_one('a[href$="/stargazers"]')
        stars = stars_el.get_text(strip=True).replace(",", "") if stars_el else "0"
        if not AI_PATTERN.search(f"{repo} {desc}"):
            continue
        items.append(
            RawItem(
                title=f"{repo}: {desc[:120]}" if desc else repo,
                url=f"https://github.com/{repo}",
                content=desc,
                extra={"stars": stars},
            )
        )
    return items


def fetch_github_trending(source) -> list:
    from app.fetchers import HTTP_TIMEOUT, USER_AGENT

    r = httpx.get(
        source.url or "https://github.com/trending?since=daily",
        headers={"User-Agent": USER_AGENT},
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
    )
    r.raise_for_status()
    return parse_trending(r.text)
