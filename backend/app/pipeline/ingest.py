"""抓取入库管道：遍历启用源 → 抓取 → 规范化去重 → 入库 → 源健康管理。"""

import hashlib
import json
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fetchers import FETCHERS, RawItem
from app.models import Item, PipelineRun, Source, utcnow

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "fbclid", "gclid"}
FAIL_THRESHOLD = 3


def normalize_url(url: str) -> str:
    try:
        p = urlparse(url.strip())
    except ValueError:
        return url.strip()
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
    path = p.path.rstrip("/") or "/"
    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, p.params, urlencode(query), ""))


def content_hash_for(raw: RawItem, source_name: str = "") -> str:
    basis = normalize_url(raw.url) if raw.url else f"{source_name}|{raw.title}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def ingest_items(session: Session, source: Source, raw_items: list[RawItem]) -> int:
    """入库去重，返回新增条数。"""
    new_count = 0
    seen_in_batch: set[str] = set()  # 同批次去重（pending 对象 select 查不到）
    for raw in raw_items:
        h = content_hash_for(raw, source.name)
        if h in seen_in_batch:
            continue
        exists = session.execute(select(Item.id).where(Item.content_hash == h)).scalar_one_or_none()
        if exists:
            continue
        seen_in_batch.add(h)
        session.add(
            Item(
                source_id=source.id,
                title=raw.title[:500],
                url=normalize_url(raw.url) if raw.url else "",
                author=raw.author[:200],
                published_at=raw.published_at,
                raw_content=raw.content,
                content_hash=h,
            )
        )
        new_count += 1
    return new_count


def run_ingest(session: Session, only_source: str | None = None) -> dict:
    run = PipelineRun(stage="ingest")
    session.add(run)
    session.commit()

    fetched = new = 0
    failed_sources: list[str] = []
    degraded_sources: list[str] = []

    query = select(Source).where(Source.enabled.is_(True))
    if only_source:
        query = select(Source).where(Source.name == only_source)
    sources = session.execute(query).scalars().all()

    for source in sources:
        fetcher = FETCHERS.get(source.fetch_method)
        if fetcher is None:
            source.status = "degraded"
            degraded_sources.append(source.name)
            continue
        try:
            raw_items = fetcher(source)
        except Exception as e:  # 单源失败隔离
            source.fail_count += 1
            if source.fail_count >= FAIL_THRESHOLD:
                source.status = "degraded"
                degraded_sources.append(source.name)
            failed_sources.append(f"{source.name}: {type(e).__name__}: {str(e)[:120]}")
            session.commit()
            continue
        source.fail_count = 0
        source.status = "ok"
        source.last_fetched_at = utcnow()
        fetched += len(raw_items)
        new += ingest_items(session, source, raw_items)
        session.commit()

    run.finished_at = utcnow()
    run.status = "success"
    run.detail = json.dumps(
        {"fetched": fetched, "new": new, "failed_sources": failed_sources, "degraded_sources": degraded_sources},
        ensure_ascii=False,
    )
    session.commit()
    return json.loads(run.detail)
