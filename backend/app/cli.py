"""命令行入口：供 GitHub Actions（或本地）一次性调用，替代常驻 FastAPI 调度。

用法：
    python -m app.cli ingest
    python -m app.cli enrich
    python -m app.cli report --type daily|weekly|monthly
    python -m app.cli export-static
    python -m app.cli deliver --type daily|weekly|monthly
    python -m app.cli all --type daily        # ingest+enrich+report+export-static+deliver 一条龙
"""

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import select

from app.config import BASE_DIR
from app.db import SessionLocal, init_db
from app.models import Enrichment, Item, Report, Source, Subscription
from app.pipeline.enrich import run_enrich
from app.pipeline.ingest import run_ingest
from app.pipeline.reports import build_daily, build_monthly, build_weekly
from app.seeds import seed_sources

BUILDERS = {"daily": build_daily, "weekly": build_weekly, "monthly": build_monthly}
STATIC_DIR = BASE_DIR / "frontend" / "public" / "data"


def _emit(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False))


def cmd_ingest(args) -> int:
    with SessionLocal() as s:
        seed_sources(s)
        _emit({"stage": "ingest", **run_ingest(s)})
    return 0


def cmd_enrich(args) -> int:
    with SessionLocal() as s:
        _emit({"stage": "enrich", **run_enrich(s)})
    return 0


def cmd_report(args) -> int:
    with SessionLocal() as s:
        seed_sources(s)
        if not args.skip_fetch:
            run_ingest(s)
            run_enrich(s)
        report = BUILDERS[args.type](s)
        _emit({"stage": "report", "type": report.type, "period": report.period_date, "title": report.title})
    return 0


def _report_dict(r: Report) -> dict:
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


def _report_meta(r: Report) -> dict:
    return {
        "type": r.type,
        "period_date": r.period_date,
        "title": r.title,
        "created_at": r.created_at.isoformat(),
        "path": f"reports/{r.type}-{r.period_date}.json",
    }


def cmd_export_static(args) -> int:
    """导出静态 JSON 端点（同源契约 §6），供 Pages 托管 + skill 连接模式消费。"""
    reports_dir = STATIC_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as s:
        reports = s.execute(select(Report).order_by(Report.created_at.desc())).scalars().all()
        index = []
        latest_by_type: dict[str, Report] = {}
        for r in reports:
            (reports_dir / f"{r.type}-{r.period_date}.json").write_text(
                json.dumps(_report_dict(r), ensure_ascii=False), encoding="utf-8"
            )
            index.append(_report_meta(r))
            if r.type not in latest_by_type:  # 已按 created_at desc 排序，首遇即最新
                latest_by_type[r.type] = r
        (reports_dir / "index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
        for type_, r in latest_by_type.items():
            (reports_dir / f"{type_}-latest.json").write_text(
                json.dumps(_report_dict(r), ensure_ascii=False), encoding="utf-8"
            )

        rows = s.execute(
            select(Item, Enrichment, Source.name)
            .join(Enrichment, Enrichment.item_id == Item.id)
            .join(Source, Source.id == Item.source_id)
            .order_by(Item.id.desc())
            .limit(200)
        ).all()
        items = [
            {
                "id": item.id,
                "title": item.title,
                "url": item.url,
                "source": source_name,
                "published_at": item.published_at.isoformat() if item.published_at else None,
                "summary_zh": enr.summary_zh,
                "category": enr.category,
                "tags": json.loads(enr.tags or "[]"),
                "entities": json.loads(enr.entities or "[]"),
                "importance_score": enr.importance_score,
            }
            for item, enr, source_name in rows
        ]
        (STATIC_DIR / "items.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    _emit({"stage": "export-static", "reports": len(index), "items": len(items), "out": str(STATIC_DIR)})
    return 0


def _sync_subscribers(session) -> None:
    """从 data/subscribers.json（手工维护邮箱列表）同步到 Subscription 表，确认态。"""
    import secrets

    path = BASE_DIR / "data" / "subscribers.json"
    if not path.exists():
        return
    emails = json.loads(path.read_text(encoding="utf-8"))
    for entry in emails:
        email = entry if isinstance(entry, str) else entry.get("email", "")
        freqs = '["daily","weekly","monthly"]' if isinstance(entry, str) else json.dumps(entry.get("frequencies", ["daily"]))
        if not email:
            continue
        existing = session.execute(select(Subscription).where(Subscription.email == email)).scalar_one_or_none()
        if existing:
            existing.confirmed = True
            existing.frequencies = freqs
        else:
            session.add(
                Subscription(
                    email=email,
                    frequencies=freqs,
                    confirmed=True,
                    confirm_token=secrets.token_urlsafe(16),
                    unsubscribe_token=secrets.token_urlsafe(16),
                )
            )
    session.commit()


def cmd_deliver(args) -> int:
    from app.delivery.email import deliver_report_email
    from app.delivery.webhook import deliver_report_webhooks

    with SessionLocal() as s:
        _sync_subscribers(s)
        r = s.execute(
            select(Report).where(Report.type == args.type).order_by(Report.created_at.desc())
        ).scalars().first()
        if not r:
            _emit({"stage": "deliver", "error": f"no {args.type} report"})
            return 1
        _emit({
            "stage": "deliver",
            "email": deliver_report_email(s, r),
            "webhooks": deliver_report_webhooks(s, r),
        })
    return 0


def cmd_all(args) -> int:
    """Actions 主路径：抓取→加工→生成→导出→分发 一条龙。"""
    rc = cmd_report(argparse.Namespace(type=args.type, skip_fetch=False))
    if rc:
        return rc
    cmd_export_static(args)
    if args.deliver:
        cmd_deliver(args)
    return 0


def main(argv=None) -> int:
    init_db()
    parser = argparse.ArgumentParser(prog="ai-intel-cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ingest")
    sub.add_parser("enrich")

    p_report = sub.add_parser("report")
    p_report.add_argument("--type", choices=BUILDERS, default="daily")
    p_report.add_argument("--skip-fetch", action="store_true", help="跳过抓取+加工，仅用现有数据组装报告")

    sub.add_parser("export-static")

    p_deliver = sub.add_parser("deliver")
    p_deliver.add_argument("--type", choices=BUILDERS, default="daily")

    p_all = sub.add_parser("all")
    p_all.add_argument("--type", choices=BUILDERS, default="daily")
    p_all.add_argument("--deliver", action="store_true", help="生成后顺带分发")

    args = parser.parse_args(argv)
    handlers = {
        "ingest": cmd_ingest,
        "enrich": cmd_enrich,
        "report": cmd_report,
        "export-static": cmd_export_static,
        "deliver": cmd_deliver,
        "all": cmd_all,
    }
    try:
        return handlers[args.cmd](args)
    except Exception as e:  # 任一失败 → 非零退出码，让 Actions 标红
        _emit({"stage": args.cmd, "error": f"{type(e).__name__}: {e}"})
        return 1


if __name__ == "__main__":
    sys.exit(main())
