"""APScheduler 定时管道：抓取 2h / 日报 07:00 / 周报周一 07:30 / 月报 1 日 08:00（Asia/Shanghai）。"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.db import SessionLocal

logger = logging.getLogger(__name__)


def job_ingest_enrich():
    from app.pipeline.enrich import run_enrich
    from app.pipeline.ingest import run_ingest

    with SessionLocal() as session:
        detail = run_ingest(session)
        logger.info("ingest: %s", detail)
        detail = run_enrich(session)
        logger.info("enrich: %s", detail)


def _deliver(session, report):
    from app.delivery.email import deliver_report_email
    from app.delivery.webhook import deliver_report_webhooks

    logger.info("email: %s", deliver_report_email(session, report))
    logger.info("webhook: %s", deliver_report_webhooks(session, report))


def job_daily():
    from app.pipeline.reports import build_daily

    job_ingest_enrich()  # 报告前补一轮抓取
    with SessionLocal() as session:
        report = build_daily(session)
        _deliver(session, report)


def job_weekly():
    from app.pipeline.reports import build_weekly

    with SessionLocal() as session:
        report = build_weekly(session)
        _deliver(session, report)


def job_monthly():
    from app.pipeline.reports import build_monthly

    with SessionLocal() as session:
        report = build_monthly(session)
        _deliver(session, report)


def create_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone=settings.timezone)
    sched.add_job(job_ingest_enrich, IntervalTrigger(hours=2), id="ingest_enrich", max_instances=1, coalesce=True)
    sched.add_job(job_daily, CronTrigger(hour=7, minute=0), id="daily", max_instances=1)
    sched.add_job(job_weekly, CronTrigger(day_of_week="mon", hour=7, minute=30), id="weekly", max_instances=1)
    sched.add_job(job_monthly, CronTrigger(day=1, hour=8, minute=0), id="monthly", max_instances=1)
    return sched
