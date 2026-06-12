"""报告组装：日报/周报/月报 → Markdown + HTML 入库 + 落盘。"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import markdown as md_lib
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import BASE_DIR, settings
from app.llm import LLMError, LLMProvider, complete_json, get_provider
from app.models import Enrichment, Item, PipelineRun, Report, Source, utcnow
from app.pipeline.analyze import deep_analyze

CATEGORY_LABELS = {
    "paradigm": "🛠 产研 AI 范式",
    "tech": "🧠 AI 技术",
    "opensource": "📦 开源项目",
    "product": "🚀 行业 AI 产品",
}
CATEGORY_ORDER = ["paradigm", "tech", "opensource", "product"]
REPORTS_DIR = BASE_DIR / "data" / "reports"

WEEKLY_PROMPT = """你是 AI 行业分析师，为关注「产研提效」与「商业产品机会」的产品经理写本周趋势综述。
以下是本周（{week_range}）全部 AI 资讯的中文摘要清单（按重要度降序）：

{digest}

输出 JSON（只输出 JSON）：
{{"highlights": "<本周大事记，3-5句话概括本周最重要的行业动向>",
 "trends": {{"paradigm": "<产研AI范式趋势，2-4句>", "tech": "<技术趋势，2-4句>",
  "opensource": "<开源热点，2-4句>", "product": "<产品与商业动向，2-4句>"}},
 "next_week_watch": ["<下周值得关注的方向1>", "<方向2>", "<方向3>"]}}"""


def _tz() -> ZoneInfo:
    return ZoneInfo(settings.timezone)


def scored_join(session: Session, since: datetime | None = None, until: datetime | None = None):
    """返回 [(Item, Enrichment, source_name)]，时间窗口按 published_at 或 created_at。"""
    q = (
        select(Item, Enrichment, Source.name)
        .join(Enrichment, Enrichment.item_id == Item.id)
        .join(Source, Source.id == Item.source_id)
    )
    rows = session.execute(q).all()
    out = []
    for item, enr, source_name in rows:
        t = item.published_at or item.created_at
        if t is not None and t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        if since and t and t < since:
            continue
        if until and t and t >= until:
            continue
        out.append((item, enr, source_name))
    out.sort(key=lambda r: r[1].importance_score, reverse=True)
    return out


def items_for_daily(session: Session, now: datetime) -> list:
    last = session.execute(
        select(Report).where(Report.type == "daily").order_by(Report.created_at.desc()).limit(1)
    ).scalar_one_or_none()
    since = last.created_at if last else now - timedelta(hours=36)
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    return scored_join(session, since=since, until=now)


def items_for_weekly(session: Session, now: datetime) -> list:
    local = now.astimezone(_tz())
    monday = (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return scored_join(session, since=monday.astimezone(timezone.utc), until=now)


def items_for_monthly(session: Session, now: datetime) -> list:
    local = now.astimezone(_tz())
    first = local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return scored_join(session, since=first.astimezone(timezone.utc), until=now)


def _degraded_sources(session: Session) -> list[str]:
    rows = session.execute(select(Source.name).where(Source.status == "degraded")).scalars().all()
    return list(rows)


def _render_item_line(item: Item, enr: Enrichment) -> str:
    tags = json.loads(enr.tags or "[]")
    tag_str = " ".join(f"`{t}`" for t in tags[:5])
    score_mark = "🔴" if enr.importance_score >= 8 else ("🟠" if enr.importance_score >= 6 else "⚪")
    return f"- {score_mark} **[{item.title}]({item.url})** ({enr.importance_score}/10)\n  {enr.summary_zh} {tag_str}"


def _render_headline(a: dict) -> str:
    actions = "\n".join(f"  - {x}" for x in a.get("action_items", []))
    return f"""### {a['headline']}

> 来源：[{a['source']}]({a['url']}) · 重要度 {a['importance']}/10

- **事件背景**：{a['background']}
- **产业影响**：{a['industry_impact']}
- **竞品对位**：{a['competitive']}
- **产研提效启示**：{a['rd_efficiency']}
- **商业机会信号**：{a['biz_opportunity']}
- **建议行动**：
{actions}
"""


def _render_categories(scored: list, per_cat_limit: int = 15) -> str:
    parts = []
    for cat in CATEGORY_ORDER:
        rows = [(i, e) for i, e, _ in scored if e.category == cat][:per_cat_limit]
        if not rows:
            continue
        lines = "\n".join(_render_item_line(i, e) for i, e in rows)
        parts.append(f"### {CATEGORY_LABELS[cat]}\n\n{lines}")
    return "\n\n".join(parts)


def _render_status(stats: dict) -> str:
    degraded = stats.get("degraded_sources", [])
    degraded_str = "、".join(degraded) if degraded else "无"
    by_cat = stats.get("by_category", {})
    cat_str = " · ".join(f"{CATEGORY_LABELS[c]} {n} 条" for c, n in by_cat.items() if n)
    return f"""## 📊 管道状态

- 本期收录 **{stats.get('total', 0)}** 条（{cat_str}）
- 降级/不可用源：{degraded_str}
"""


def _to_html(markdown_text: str) -> str:
    return md_lib.markdown(markdown_text, extensions=["tables", "fenced_code"])


def _persist(session: Session, type_: str, period_date: str, title: str, markdown_text: str, headlines: list, stats: dict) -> Report:
    html = _to_html(markdown_text)
    existing = session.execute(
        select(Report).where(Report.type == type_, Report.period_date == period_date)
    ).scalar_one_or_none()
    if existing:
        existing.title = title
        existing.markdown = markdown_text
        existing.html = html
        existing.headline_analysis = json.dumps(headlines, ensure_ascii=False)
        existing.stats = json.dumps(stats, ensure_ascii=False)
        report = existing
    else:
        report = Report(
            type=type_,
            period_date=period_date,
            title=title,
            markdown=markdown_text,
            html=html,
            headline_analysis=json.dumps(headlines, ensure_ascii=False),
            stats=json.dumps(stats, ensure_ascii=False),
        )
        session.add(report)
    session.commit()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / f"{type_}-{period_date}.md").write_text(markdown_text, encoding="utf-8")
    return report


def _stats_for(scored: list, session: Session) -> dict:
    by_cat: dict[str, int] = {}
    for _, e, _ in scored:
        by_cat[e.category] = by_cat.get(e.category, 0) + 1
    return {"total": len(scored), "by_category": by_cat, "degraded_sources": _degraded_sources(session)}


def build_daily(session: Session, date_str: str | None = None, provider: LLMProvider | None = None, now: datetime | None = None) -> Report:
    provider = provider or get_provider()
    now = now or utcnow()
    date_str = date_str or now.astimezone(_tz()).strftime("%Y-%m-%d")
    run = PipelineRun(stage="report_daily")
    session.add(run)
    session.commit()

    scored = items_for_daily(session, now)
    headlines = deep_analyze(session, provider, scored, top_n=5, min_score=7)
    stats = _stats_for(scored, session)

    title = f"AI 情报日报 · {date_str}"
    parts = [f"# {title}\n"]
    if headlines:
        parts.append("## 🔥 今日头条\n")
        parts.extend(_render_headline(a) for a in headlines)
    elif scored:
        top = scored[:5]
        parts.append("## 🔥 今日高分条目\n")
        parts.extend(_render_item_line(i, e) for i, e, _ in top)
    categories_md = _render_categories(scored)
    parts.append(f"## 📋 分类速览\n\n{categories_md}" if categories_md else "_本期暂无新条目_")
    parts.append(_render_status(stats))
    markdown_text = "\n\n".join(parts)

    report = _persist(session, "daily", date_str, title, markdown_text, headlines, stats)
    run.finished_at = utcnow()
    run.status = "success"
    run.detail = json.dumps({"items": stats["total"], "headlines": len(headlines)})
    session.commit()
    return report


def _week_str(now: datetime) -> str:
    local = now.astimezone(_tz())
    iso = local.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def build_weekly(session: Session, week_str: str | None = None, provider: LLMProvider | None = None, now: datetime | None = None) -> Report:
    provider = provider or get_provider()
    now = now or utcnow()
    week_str = week_str or _week_str(now)
    run = PipelineRun(stage="report_weekly")
    session.add(run)
    session.commit()

    scored = items_for_weekly(session, now)
    stats = _stats_for(scored, session)
    local = now.astimezone(_tz())
    monday = (local - timedelta(days=local.weekday())).strftime("%m-%d")
    week_range = f"{monday} ~ {local.strftime('%m-%d')}"

    trends: dict = {}
    if scored:
        digest = "\n".join(
            f"[{e.category}] {e.summary_zh} (重要度{e.importance_score})" for _, e, _ in scored[:120]
        )
        try:
            trends = complete_json(provider, WEEKLY_PROMPT.format(week_range=week_range, digest=digest), tier="deep")
        except LLMError:
            trends = {}

    big_events = [(i, e, s) for i, e, s in scored if e.importance_score >= 8]
    top10 = scored[:10]

    title = f"AI 情报周报 · {week_str}（{week_range}）"
    parts = [f"# {title}\n"]
    if trends.get("highlights"):
        parts.append(f"## 🗞 本周大事记\n\n{trends['highlights']}")
    if big_events:
        parts.append("## 🔴 本周重大事件\n\n" + "\n".join(_render_item_line(i, e) for i, e, _ in big_events[:10]))
    t = trends.get("trends", {})
    if t:
        trend_lines = "\n\n".join(f"### {CATEGORY_LABELS[c]}\n\n{t[c]}" for c in CATEGORY_ORDER if t.get(c))
        parts.append(f"## 📈 四维趋势综述\n\n{trend_lines}")
    if trends.get("next_week_watch"):
        watch = "\n".join(f"- {w}" for w in trends["next_week_watch"])
        parts.append(f"## 🔭 下周关注\n\n{watch}")
    if top10:
        parts.append("## 🏆 本周高分 Top 10\n\n" + "\n".join(_render_item_line(i, e) for i, e, _ in top10))
    parts.append(_render_status(stats))
    markdown_text = "\n\n".join(parts)

    report = _persist(session, "weekly", week_str, title, markdown_text, [], {**stats, "trends": trends})
    run.finished_at = utcnow()
    run.status = "success"
    run.detail = json.dumps({"items": stats["total"]})
    session.commit()
    return report


def build_monthly(session: Session, month_str: str | None = None, provider: LLMProvider | None = None, now: datetime | None = None) -> Report:
    provider = provider or get_provider()
    now = now or utcnow()
    month_str = month_str or now.astimezone(_tz()).strftime("%Y-%m")
    run = PipelineRun(stage="report_monthly")
    session.add(run)
    session.commit()

    scored = items_for_monthly(session, now)
    stats = _stats_for(scored, session)

    trends: dict = {}
    if scored:
        digest = "\n".join(
            f"[{e.category}] {e.summary_zh} (重要度{e.importance_score})" for _, e, _ in scored[:150]
        )
        try:
            trends = complete_json(provider, WEEKLY_PROMPT.format(week_range=month_str, digest=digest), tier="deep")
        except LLMError:
            trends = {}

    title = f"AI 情报月报 · {month_str}"
    parts = [f"# {title}\n"]
    if trends.get("highlights"):
        parts.append(f"## 🗞 本月综述\n\n{trends['highlights']}")
    big_events = [(i, e, s) for i, e, s in scored if e.importance_score >= 8]
    if big_events:
        parts.append("## 🔴 本月重大事件时间线\n\n" + "\n".join(_render_item_line(i, e) for i, e, _ in big_events[:20]))
    t = trends.get("trends", {})
    if t:
        trend_lines = "\n\n".join(f"### {CATEGORY_LABELS[c]}\n\n{t[c]}" for c in CATEGORY_ORDER if t.get(c))
        parts.append(f"## 📈 月度趋势研判\n\n{trend_lines}")
    if trends.get("next_week_watch"):
        watch = "\n".join(f"- {w}" for w in trends["next_week_watch"])
        parts.append(f"## 🔭 下月关注方向\n\n{watch}")
    parts.append(_render_status(stats))
    markdown_text = "\n\n".join(parts)

    report = _persist(session, "monthly", month_str, title, markdown_text, [], {**stats, "trends": trends})
    run.finished_at = utcnow()
    run.status = "success"
    run.detail = json.dumps({"items": stats["total"]})
    session.commit()
    return report
