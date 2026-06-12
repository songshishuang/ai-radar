import pytest
import sqlalchemy.exc

from app import models
from app.models import Item, Source


def test_tables_create(db_session):
    names = {t.name for t in models.Base.metadata.sorted_tables}
    assert {
        "sources",
        "items",
        "enrichments",
        "reports",
        "subscriptions",
        "delivery_logs",
        "pipeline_runs",
    } <= names


def test_item_unique_hash(db_session):
    s = Source(name="x", category="vendor", url="http://a", fetch_method="rss")
    db_session.add(s)
    db_session.flush()
    db_session.add(Item(source_id=s.id, title="t", url="http://a/1", content_hash="h1"))
    db_session.flush()
    db_session.add(Item(source_id=s.id, title="t2", url="http://a/2", content_hash="h1"))
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.flush()


def test_report_unique_per_period(db_session):
    from app.models import Report

    db_session.add(Report(type="daily", period_date="2026-06-12", title="d", markdown="m", html="h"))
    db_session.flush()
    db_session.add(Report(type="weekly", period_date="2026-06-12", title="w", markdown="m", html="h"))
    db_session.flush()  # 不同 type 同日期 OK
    db_session.add(Report(type="daily", period_date="2026-06-12", title="dup", markdown="m", html="h"))
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.flush()
