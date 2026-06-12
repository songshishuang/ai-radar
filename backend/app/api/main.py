"""FastAPI 应用：REST API + RSS 输出 + 管理端点 + 调度器生命周期。"""

import json
import secrets
from contextlib import asynccontextmanager
from email.utils import format_datetime
from xml.sax.saxutils import escape

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal, init_db
from app.models import Enrichment, Item, PipelineRun, Report, Source, Subscription


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    init_db()
    with SessionLocal() as session:
        from app.seeds import seed_sources

        seed_sources(session)
    if settings.scheduler_enabled:
        from app.scheduler import create_scheduler

        _scheduler = create_scheduler()
        _scheduler.start()
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)


app = FastAPI(title="AI Intel", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", settings.site_base_url],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Reports ──


@app.get("/api/reports")
def list_reports(type: str | None = None, limit: int = Query(20, le=100), db: Session = Depends(get_db)):
    q = select(Report).order_by(Report.created_at.desc()).limit(limit)
    if type:
        q = select(Report).where(Report.type == type).order_by(Report.created_at.desc()).limit(limit)
    rows = db.execute(q).scalars().all()
    return [
        {"id": r.id, "type": r.type, "period_date": r.period_date, "title": r.title, "created_at": r.created_at.isoformat()}
        for r in rows
    ]


@app.get("/api/reports/{type}/{period_date}")
def get_report(type: str, period_date: str, db: Session = Depends(get_db)):
    r = db.execute(select(Report).where(Report.type == type, Report.period_date == period_date)).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "report not found")
    return {
        "id": r.id,
        "type": r.type,
        "period_date": r.period_date,
        "title": r.title,
        "markdown": r.markdown,
        "html": r.html,
        "headline_analysis": r.headline_analysis,
        "stats": r.stats,
        "created_at": r.created_at.isoformat(),
    }


# ── Items ──


@app.get("/api/items")
def list_items(
    category: str | None = None,
    source: str | None = None,
    q: str | None = None,
    min_score: int | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = (
        select(Item, Enrichment, Source.name)
        .join(Enrichment, Enrichment.item_id == Item.id)
        .join(Source, Source.id == Item.source_id)
        .order_by(Item.id.desc())
    )
    if category:
        query = query.where(Enrichment.category == category)
    if source:
        query = query.where(Source.name == source)
    if min_score:
        query = query.where(Enrichment.importance_score >= min_score)
    if q:
        like = f"%{q}%"
        query = query.where(or_(Item.title.like(like), Enrichment.summary_zh.like(like)))
    rows = db.execute(query.limit(limit).offset(offset)).all()
    return [
        {
            "id": item.id,
            "title": item.title,
            "url": item.url,
            "source": source_name,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "summary_zh": enr.summary_zh,
            "category": enr.category,
            "tags": json.loads(enr.tags or "[]"),
            "importance_score": enr.importance_score,
        }
        for item, enr, source_name in rows
    ]


# ── Subscriptions ──


class SubscribeBody(BaseModel):
    email: EmailStr
    frequencies: list[str] = ["daily"]


@app.post("/api/subscriptions", status_code=201)
def create_subscription(body: SubscribeBody, db: Session = Depends(get_db)):
    freqs = [f for f in body.frequencies if f in {"daily", "weekly", "monthly"}] or ["daily"]
    existing = db.execute(select(Subscription).where(Subscription.email == body.email)).scalar_one_or_none()
    if existing:
        existing.frequencies = json.dumps(freqs)
        sub = existing
    else:
        sub = Subscription(
            email=body.email,
            frequencies=json.dumps(freqs),
            confirm_token=secrets.token_urlsafe(24),
            unsubscribe_token=secrets.token_urlsafe(24),
        )
        db.add(sub)
    db.commit()
    from app.delivery.email import send_confirm_email

    mailed = send_confirm_email(db, sub)
    return {"message": "确认邮件已发送，请查收" if mailed else "订阅已登记（SMTP 未配置，可由管理员确认）"}


@app.get("/api/subscriptions/confirm")
def confirm_subscription(token: str, db: Session = Depends(get_db)):
    sub = db.execute(select(Subscription).where(Subscription.confirm_token == token)).scalar_one_or_none()
    if not sub:
        raise HTTPException(404, "invalid token")
    sub.confirmed = True
    db.commit()
    return {"message": f"{sub.email} 订阅已确认"}


@app.get("/api/subscriptions/unsubscribe")
def unsubscribe(token: str, db: Session = Depends(get_db)):
    sub = db.execute(select(Subscription).where(Subscription.unsubscribe_token == token)).scalar_one_or_none()
    if not sub:
        raise HTTPException(404, "invalid token")
    db.delete(sub)
    db.commit()
    return {"message": "已退订"}


# ── RSS ──


def _rss_xml(title: str, link: str, entries: list[dict]) -> str:
    items_xml = "".join(
        f"<item><title>{escape(e['title'])}</title><link>{escape(e['link'])}</link>"
        f"<guid isPermaLink=\"false\">{escape(e['guid'])}</guid>"
        + (f"<pubDate>{e['pub']}</pubDate>" if e.get("pub") else "")
        + f"<description>{escape(e['desc'][:800])}</description></item>"
        for e in entries
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>{escape(title)}</title><link>{escape(link)}</link><description>{escape(title)}</description>"
        f"{items_xml}</channel></rss>"
    )


@app.get("/rss/feed.xml")
def rss_feed(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Item, Enrichment)
        .join(Enrichment, Enrichment.item_id == Item.id)
        .order_by(Item.id.desc())
        .limit(100)
    ).all()
    entries = [
        {
            "title": item.title,
            "link": item.url or f"{settings.site_base_url}/feed",
            "guid": item.content_hash,
            "pub": format_datetime(item.published_at) if item.published_at else None,
            "desc": enr.summary_zh,
        }
        for item, enr in rows
    ]
    return Response(_rss_xml("AI 情报站 · 全量条目", settings.site_base_url, entries), media_type="application/rss+xml")


@app.get("/rss/{kind}.xml")
def rss_reports(kind: str, db: Session = Depends(get_db)):
    if kind not in {"daily", "weekly", "monthly"}:
        raise HTTPException(404)
    rows = (
        db.execute(select(Report).where(Report.type == kind).order_by(Report.created_at.desc()).limit(20))
        .scalars()
        .all()
    )
    entries = [
        {
            "title": r.title,
            "link": f"{settings.site_base_url.rstrip('/')}/reports/{r.type}/{r.period_date}",
            "guid": f"{r.type}-{r.period_date}",
            "pub": format_datetime(r.created_at),
            "desc": r.markdown[:800],
        }
        for r in rows
    ]
    return Response(_rss_xml(f"AI 情报站 · {kind} 报告", settings.site_base_url, entries), media_type="application/rss+xml")


# ── Admin ──


def admin_guard(authorization: str = Header(default="")):
    if authorization != f"Bearer {settings.admin_token}":
        raise HTTPException(401, "unauthorized")


@app.post("/api/admin/run/{stage}", dependencies=[Depends(admin_guard)])
def admin_run(stage: str, db: Session = Depends(get_db)):
    if stage == "ingest":
        from app.pipeline.ingest import run_ingest

        return run_ingest(db)
    if stage == "enrich":
        from app.pipeline.enrich import run_enrich

        return run_enrich(db)
    if stage == "daily":
        from app.pipeline.reports import build_daily

        r = build_daily(db)
        return {"report": r.period_date, "title": r.title}
    if stage == "weekly":
        from app.pipeline.reports import build_weekly

        r = build_weekly(db)
        return {"report": r.period_date, "title": r.title}
    if stage == "monthly":
        from app.pipeline.reports import build_monthly

        r = build_monthly(db)
        return {"report": r.period_date, "title": r.title}
    if stage == "deliver-latest-daily":
        from app.delivery.email import deliver_report_email
        from app.delivery.webhook import deliver_report_webhooks

        r = db.execute(select(Report).where(Report.type == "daily").order_by(Report.created_at.desc())).scalars().first()
        if not r:
            raise HTTPException(404, "no daily report")
        return {"email": deliver_report_email(db, r), "webhooks": deliver_report_webhooks(db, r)}
    raise HTTPException(404, "unknown stage")


@app.get("/api/admin/status", dependencies=[Depends(admin_guard)])
def admin_status(db: Session = Depends(get_db)):
    sources = db.execute(select(Source)).scalars().all()
    runs = db.execute(select(PipelineRun).order_by(PipelineRun.id.desc()).limit(10)).scalars().all()
    total_cost = sum(e.cost_usd for e in db.execute(select(Enrichment)).scalars().all())
    item_count = db.execute(select(Item.id)).all()
    return {
        "sources": [
            {"name": s.name, "category": s.category, "enabled": s.enabled, "status": s.status, "fail_count": s.fail_count}
            for s in sources
        ],
        "recent_runs": [
            {"stage": r.stage, "status": r.status, "started_at": r.started_at.isoformat(), "detail": json.loads(r.detail or "{}")}
            for r in runs
        ],
        "items_total": len(item_count),
        "cost_usd_total": round(total_cost, 4),
    }
