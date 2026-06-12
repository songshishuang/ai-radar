"""Enrich 管道：批量调 LLM（fast tier）生成中文摘要/分类/标签/重要度。"""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.llm import LLMError, LLMProvider, complete_json, get_provider
from app.models import Enrichment, Item, PipelineRun, Source, utcnow

VALID_CATEGORIES = {"paradigm", "tech", "opensource", "product"}

BATCH_PROMPT = """你是 AI 行业分析师。对下列 {n} 条英文 AI 资讯逐条输出 JSON。
分类 category 四选一：paradigm(产研AI范式/研发提效工具) | tech(模型与技术) | opensource(开源项目) | product(行业AI产品/商业动态)。
importance 1-10：重大发布/范式变化 8-10；值得关注 5-7；一般 1-4。
对产品经理视角特别相关的（产研提效工具、商业机会信号）评分上浮 1 分。
输出格式（只输出 JSON 数组，无其他文字）：
[{{"id": <原id>, "summary_zh": "<80-150字中文摘要>", "category": "...", "tags": ["...", "..."], "importance": <1-10整数>}}]

条目：
{entries}"""


def _format_entry(item: Item, source_name: str) -> str:
    content = (item.raw_content or "")[:400].replace("\n", " ")
    return f"{item.id} | {item.title} | 来源:{source_name} | {content}"


def enrich_batch(session: Session, provider: LLMProvider, items: list[Item], source_names: dict[int, str]) -> int:
    entries = "\n".join(_format_entry(i, source_names.get(i.source_id, "?")) for i in items)
    prompt = BATCH_PROMPT.format(n=len(items), entries=entries)
    results = complete_json(provider, prompt, tier="fast")
    if not isinstance(results, list):
        raise LLMError("batch result is not a list")

    by_id = {i.id: i for i in items}
    created = 0
    for r in results:
        item = by_id.get(r.get("id"))
        if item is None:
            continue
        category = r.get("category", "tech")
        if category not in VALID_CATEGORIES:
            category = "tech"
        importance = r.get("importance", 5)
        importance = max(1, min(10, int(importance) if str(importance).isdigit() else 5))
        session.add(
            Enrichment(
                item_id=item.id,
                summary_zh=str(r.get("summary_zh", ""))[:1000],
                category=category,
                tags=json.dumps(r.get("tags", [])[:8], ensure_ascii=False),
                importance_score=importance,
                model=settings.llm_fast_model,
            )
        )
        created += 1
    session.commit()
    return created


def run_enrich(
    session: Session, batch_size: int = 12, provider: LLMProvider | None = None, max_age_days: int = 7
) -> dict:
    """只处理时间窗口内（published_at 或 created_at 距今 ≤ max_age_days）的未加工条目，
    避免首抓时 RSS 历史存量挤爆 LLM 配额。"""
    from datetime import timedelta

    provider = provider or get_provider()
    run = PipelineRun(stage="enrich")
    session.add(run)
    session.commit()

    candidates = (
        session.execute(
            select(Item).outerjoin(Enrichment, Enrichment.item_id == Item.id).where(Enrichment.id.is_(None)).order_by(Item.id)
        )
        .scalars()
        .all()
    )
    cutoff = utcnow() - timedelta(days=max_age_days)
    pending = []
    for item in candidates:
        t = item.published_at or item.created_at
        if t is not None and t.tzinfo is None:
            from datetime import timezone as _tz

            t = t.replace(tzinfo=_tz.utc)
        if t is None or t >= cutoff:
            pending.append(item)
    source_names = {s.id: s.name for s in session.execute(select(Source)).scalars().all()}

    enriched = 0
    failed_batches = 0
    for i in range(0, len(pending), batch_size):
        batch = pending[i : i + batch_size]
        try:
            enriched += enrich_batch(session, provider, batch, source_names)
        except LLMError:
            failed_batches += 1
            session.rollback()
            continue

    run.finished_at = utcnow()
    run.status = "success" if failed_batches == 0 else ("failed" if enriched == 0 and pending else "success")
    run.detail = json.dumps({"pending": len(pending), "enriched": enriched, "failed_batches": failed_batches})
    session.commit()
    return json.loads(run.detail)
