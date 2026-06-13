"""把 SQLite 里的报告 + 条目导出为前端可在构建期读取的静态 JSON + 静态 RSS。

用法：
    INTEL_DB_URL=sqlite:///../data/intel.db \
    SITE_BASE=https://songshishuang.github.io/ai-radar \
    .venv/bin/python export_static.py

产出：
    frontend/content/reports.json              # 全部报告元信息（倒序）
    frontend/content/report-{type}-{date}.json # 每份报告全文
    frontend/content/items.json                # 全部加工条目（倒序）
    frontend/public/rss/{daily,weekly,monthly,feed}.xml
"""

import json
import os
import sys
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import Enrichment, Item, Report, Source  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "frontend" / "content"
RSS_DIR = REPO_ROOT / "frontend" / "public" / "rss"

SITE_BASE = os.environ.get("SITE_BASE", "https://songshishuang.github.io/ai-radar").rstrip("/")
# 把旧报告 HTML/Markdown 里写死的本地地址替换为生产地址
LOCAL_BASES = ["http://localhost:3000", "http://127.0.0.1:3000"]


def _fix_links(text: str) -> str:
    if not text:
        return text
    for local in LOCAL_BASES:
        text = text.replace(local, SITE_BASE)
    return text


def export_reports(session) -> int:
    reports = session.execute(select(Report).order_by(Report.created_at.desc())).scalars().all()
    index = []
    for r in reports:
        index.append(
            {
                "id": r.id,
                "type": r.type,
                "period_date": r.period_date,
                "title": r.title,
                "created_at": r.created_at.isoformat(),
            }
        )
        detail = {
            "id": r.id,
            "type": r.type,
            "period_date": r.period_date,
            "title": r.title,
            "markdown": _fix_links(r.markdown),
            "html": _fix_links(r.html),
            "headline_analysis": _fix_links(r.headline_analysis or "[]"),
            "stats": r.stats or "{}",
            "created_at": r.created_at.isoformat(),
        }
        (CONTENT_DIR / f"report-{r.type}-{r.period_date}.json").write_text(
            json.dumps(detail, ensure_ascii=False), encoding="utf-8"
        )
    (CONTENT_DIR / "reports.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return len(reports)


def export_items(session) -> int:
    rows = session.execute(
        select(Item, Enrichment, Source.name)
        .join(Enrichment, Enrichment.item_id == Item.id)
        .join(Source, Source.id == Item.source_id)
        .order_by(Item.id.desc())
    ).all()
    items = [
        {
            "id": item.id,
            "title": item.title,
            "url": item.url,
            "source": source_name,
            "published_at": item.published_at.isoformat() if item.published_at else "",
            "summary_zh": enr.summary_zh,
            "category": enr.category,
            "tags": json.loads(enr.tags or "[]"),
            "entities": json.loads(enr.entities or "[]"),
            "importance_score": enr.importance_score,
        }
        for item, enr, source_name in rows
    ]
    (CONTENT_DIR / "items.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return len(items)


def _rss(title: str, entries: list[dict]) -> str:
    items_xml = "".join(
        f"<item><title>{escape(e['title'])}</title><link>{escape(e['link'])}</link>"
        f'<guid isPermaLink="false">{escape(e["guid"])}</guid>'
        + (f"<pubDate>{e['pub']}</pubDate>" if e.get("pub") else "")
        + f"<description>{escape(e['desc'][:800])}</description></item>"
        for e in entries
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>{escape(title)}</title><link>{escape(SITE_BASE)}</link>"
        f"<description>{escape(title)}</description>{items_xml}</channel></rss>"
    )


def export_rss(session) -> None:
    for kind in ("daily", "weekly", "monthly"):
        reports = (
            session.execute(select(Report).where(Report.type == kind).order_by(Report.created_at.desc()).limit(20))
            .scalars()
            .all()
        )
        entries = [
            {
                "title": r.title,
                "link": f"{SITE_BASE}/reports/{r.type}/{r.period_date}/",
                "guid": f"{r.type}-{r.period_date}",
                "pub": format_datetime(r.created_at),
                "desc": _fix_links(r.markdown)[:800],
            }
            for r in reports
        ]
        (RSS_DIR / f"{kind}.xml").write_text(_rss(f"AI 情报站 · {kind} 报告", entries), encoding="utf-8")

    rows = session.execute(
        select(Item, Enrichment).join(Enrichment, Enrichment.item_id == Item.id).order_by(Item.id.desc()).limit(100)
    ).all()
    feed_entries = [
        {
            "title": item.title,
            "link": item.url or SITE_BASE,
            "guid": item.content_hash,
            "pub": format_datetime(item.published_at) if item.published_at else None,
            "desc": enr.summary_zh,
        }
        for item, enr in rows
    ]
    (RSS_DIR / "feed.xml").write_text(_rss("AI 情报站 · 全量条目", feed_entries), encoding="utf-8")


def main() -> None:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    RSS_DIR.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as session:
        n_reports = export_reports(session)
        n_items = export_items(session)
        export_rss(session)
    print(f"exported: {n_reports} reports, {n_items} items, RSS → {RSS_DIR}")
    print(f"site base: {SITE_BASE}")


if __name__ == "__main__":
    main()
