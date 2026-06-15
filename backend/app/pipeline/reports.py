"""报告组装：日报/周报/月报 → Markdown + HTML 入库 + 落盘。"""

import json
import re
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
    "model-release": "🧠 模型发布",
    "dev-tooling": "🛠 产研工具",
    "agent-infra": "🔧 Agent 基建",
    "research": "🔬 前沿研究",
    "opensource": "📦 开源生态",
    "product-launch": "🚀 产品动态",
    "business": "💰 商业资本",
    "policy-safety": "🛡 政策安全",
}
CATEGORY_ORDER = [
    "model-release",
    "dev-tooling",
    "agent-infra",
    "research",
    "opensource",
    "product-launch",
    "business",
    "policy-safety",
]

TLDR_PROMPT = """基于以下今日 AI 行业高分资讯摘要，写一段「今日速览」：恰好 3 句话，每句一个重点，合计不超过 120 字。直接输出文本，不要 JSON、不要列表符号。

{digest}"""
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
    # 标题级去重：同一事件多源转载 / 同源带不同追踪参数旧重复，按规范化标题合并，保留最高分（已降序→首现即最高）
    seen_titles: set[str] = set()
    deduped = []
    for item, enr, source_name in out:
        key = re.sub(r"\s+", "", (item.title or "").lower())
        if key and key in seen_titles:
            continue
        seen_titles.add(key)
        deduped.append((item, enr, source_name))
    return deduped


def items_for_daily(session: Session, now: datetime, period_date: str | None = None) -> list:
    """滚动最近 36h（与 ai-radar fetch --since 36h 一致），不依赖上份日报生成时刻。
    旧逻辑用『上份日报 created_at』作 since + scored_join 按 published_at 过滤，会把
    『发布于昨天白天、今早才抓到』的条目全部排除（同日多次重建时窗口更几乎归零），
    导致条目骤减 → 深度分析降级。滚动窗口让每次跑都覆盖最近 36h 发布的全部资讯。"""
    since = now - timedelta(hours=36)
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    return scored_join(session, since=since, until=now)


def items_for_weekly(session: Session, now: datetime) -> list:
    # 滚动最近 7 天：任何一天生成的周报都是完整一周（周一打开即含上周）
    return scored_join(session, since=now - timedelta(days=7), until=now)


def items_for_monthly(session: Session, now: datetime) -> list:
    # 滚动最近 30 天：任何一天生成的月报都是完整一月（月初打开即含上月）
    return scored_join(session, since=now - timedelta(days=30), until=now)


def _degraded_sources(session: Session) -> list[str]:
    rows = session.execute(select(Source.name).where(Source.status == "degraded")).scalars().all()
    return list(rows)


def _render_item_line(item: Item, enr: Enrichment) -> str:
    tags = json.loads(enr.tags or "[]")
    tag_str = " ".join(f"`{t}`" for t in tags[:5])
    score_mark = "🔴" if enr.importance_score >= 8 else ("🟠" if enr.importance_score >= 6 else "⚪")
    return f"- {score_mark} **[{item.title}]({item.url})** ({enr.importance_score}/10)\n  {enr.summary_zh} {tag_str}"


def _render_headline_brief(a: dict, idx: int) -> str:
    """正文必读区：3 行极简（标题 / so-what 结论 / 首条行动）。"""
    so_what = a.get("so_what") or (a.get("background", "").split("。")[0] + "。")
    first_action = (a.get("action_items") or [""])[0]
    action_line = f"\n👉 {first_action}" if first_action else ""
    return f"""**{idx}. [{a['headline']}]({a['url']})** `{a['importance']}/10` · {a['source']}
⚡ {so_what}{action_line}"""


def _render_headline_full(a: dict) -> str:
    """附录区：六段全文。"""
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


def _render_brief_line(item: Item, enr: Enrichment, source_name: str) -> str:
    """值得关注区：仅一行（标题+分数+分类+来源），摘要不进正文（网页 feed 可看）。"""
    return f"- **[{item.title}]({item.url})** `{enr.importance_score}` · {CATEGORY_LABELS.get(enr.category, enr.category)} · {source_name}"


def build_daily(session: Session, date_str: str | None = None, provider: LLMProvider | None = None, now: datetime | None = None) -> Report:
    """金字塔结构：⚡速览(3句) → 🔥必读 Top3-5(深度研报,≥8分) → 📌值得关注(6-7分,≤12条一行式) → 尾注收录。"""
    provider = provider or get_provider()
    now = now or utcnow()
    date_str = date_str or now.astimezone(_tz()).strftime("%Y-%m-%d")
    run = PipelineRun(stage="report_daily")
    session.add(run)
    session.commit()

    scored = items_for_daily(session, now, period_date=date_str)
    headlines = deep_analyze(session, provider, scored, top_n=5, min_score=8)
    if not headlines:  # ≥8 无果时放宽到 ≥7，保证必读区不空
        headlines = deep_analyze(session, provider, scored, top_n=3, min_score=7)
    stats = _stats_for(scored, session)

    headline_ids = {a["item_id"] for a in headlines}
    notable = [(i, e, s) for i, e, s in scored if e.importance_score in (6, 7) and i.id not in headline_ids][:8]
    shown = len(headlines) + len(notable)
    rest = max(0, stats["total"] - shown)

    tldr = ""
    if scored:
        digest = "\n".join(f"- {e.summary_zh}" for _, e, _ in scored[:15])
        try:
            tldr = provider.complete(TLDR_PROMPT.format(digest=digest), tier="fast").strip()
            # claude-cli 子进程可能受用户全局 CLAUDE.md 影响输出称呼/引言行，剥离之
            tldr = re.sub(r"^My Lord[，,：:]?\s*", "", tldr)
            tldr = re.sub(r"^[^。\n]{0,24}(如下|以下是[^。\n]{0,12})[：:]\s*\n*", "", tldr).strip()[:300]
        except Exception:
            tldr = ""
    stats["tldr"] = tldr

    title = f"AI 情报日报 · {date_str}"
    parts = [f"# {title}\n\n_☕ 正文 2 分钟读完 · 深度解读见文末附录_"]
    if tldr:
        parts.append(f"## ⚡ 今日速览\n\n{tldr}")
    if headlines:
        brief = "\n\n".join(_render_headline_brief(a, idx) for idx, a in enumerate(headlines, 1))
        parts.append(f"## 🔥 今日必读\n\n{brief}")
    elif scored:
        parts.append("## 🔥 今日高分条目\n\n" + "\n".join(_render_item_line(i, e) for i, e, _ in scored[:5]))
    if notable:
        parts.append("## 📌 值得关注\n\n" + "\n".join(_render_brief_line(i, e, s) for i, e, s in notable))
    if not scored:
        parts.append("_本期暂无新条目_")
    footer_bits = [f"本期共收录 **{stats['total']}** 条"]
    if rest:
        footer_bits.append(f"其余 {rest} 条见[网站信息流]({settings.site_base_url}/feed)")
    degraded = stats.get("degraded_sources", [])
    if degraded:
        footer_bits.append(f"降级源 {len(degraded)} 个")
    parts.append("---\n\n_" + " · ".join(footer_bits) + "_")
    if headlines:  # 深度全文沉底，想深入再往下滚
        parts.append("## 📚 附录 · 深度解读\n\n" + "\n\n".join(_render_headline_full(a) for a in headlines))
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
    start = (local - timedelta(days=7)).strftime("%m-%d")
    week_range = f"{start} ~ {local.strftime('%m-%d')}"

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
    big_ids = {i.id for i, _, _ in big_events[:10]}
    top10 = [(i, e, s) for i, e, s in scored if i.id not in big_ids][:10]

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
        parts.append("## 🏆 本周其他高分条目\n\n" + "\n".join(_render_item_line(i, e) for i, e, _ in top10))
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
