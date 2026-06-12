import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.api import main as api_main
from app.config import settings
from app.models import DeliveryLog, Enrichment, Item, Report, Source, Subscription


@pytest.fixture()
def client(db_session, monkeypatch):
    monkeypatch.setattr(settings, "scheduler_enabled", False)
    app = api_main.app

    def override_db():
        yield db_session

    app.dependency_overrides[api_main.get_db] = override_db
    # 绕过 lifespan（init_db/seed 用真实 DB），直接用 TestClient 不触发 startup 的方式：
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_report(db_session):
    r = Report(type="daily", period_date="2026-06-12", title="AI 情报日报 · 2026-06-12", markdown="# hi", html="<h1>hi</h1>")
    db_session.add(r)
    db_session.commit()
    return r


def _seed_item(db_session):
    s = Source(name="api-src", category="vendor", url="http://s", fetch_method="rss")
    db_session.add(s)
    db_session.flush()
    it = Item(source_id=s.id, title="Hello AI", url="https://x.com/hello", content_hash="apih1", published_at=datetime.now(timezone.utc))
    db_session.add(it)
    db_session.flush()
    db_session.add(Enrichment(item_id=it.id, summary_zh="你好摘要", category="model-release", tags='["LLM"]', entities='["OpenAI"]', importance_score=8))
    db_session.commit()


def test_reports_list_and_detail(client, db_session):
    _seed_report(db_session)
    rows = client.get("/api/reports?type=daily").json()
    assert rows[0]["period_date"] == "2026-06-12"
    detail = client.get("/api/reports/daily/2026-06-12").json()
    assert detail["html"] == "<h1>hi</h1>"
    assert client.get("/api/reports/daily/1999-01-01").status_code == 404


def test_items_filters(client, db_session):
    _seed_item(db_session)
    assert len(client.get("/api/items").json()) == 1
    assert len(client.get("/api/items?category=model-release&min_score=7").json()) == 1
    assert len(client.get("/api/items?category=business").json()) == 0
    assert len(client.get("/api/items?q=你好").json()) == 1
    assert client.get("/api/items?q=不存在的词").json() == []


def test_subscription_flow(client, db_session):
    r = client.post("/api/subscriptions", json={"email": "a@b.com", "frequencies": ["daily", "weekly", "bogus"]})
    assert r.status_code == 201
    sub = db_session.query(Subscription).filter_by(email="a@b.com").one()
    assert json.loads(sub.frequencies) == ["daily", "weekly"]
    assert not sub.confirmed
    assert client.get(f"/api/subscriptions/confirm?token={sub.confirm_token}").status_code == 200
    db_session.refresh(sub)
    assert sub.confirmed
    assert client.get(f"/api/subscriptions/unsubscribe?token={sub.unsubscribe_token}").status_code == 200
    assert db_session.query(Subscription).count() == 0


def test_rss_outputs(client, db_session):
    _seed_report(db_session)
    _seed_item(db_session)
    r = client.get("/rss/daily.xml")
    assert r.status_code == 200
    assert r.text.startswith("<?xml")
    assert "AI 情报日报" in r.text
    feed = client.get("/rss/feed.xml")
    assert "Hello AI" in feed.text
    assert client.get("/rss/bogus.xml").status_code == 404


def test_admin_auth_and_status(client, db_session):
    assert client.get("/api/admin/status").status_code == 401
    r = client.get("/api/admin/status", headers={"Authorization": f"Bearer {settings.admin_token}"})
    assert r.status_code == 200
    assert "sources" in r.json()


def test_delivery_email_skipped_without_smtp(db_session):
    from app.delivery.email import deliver_report_email

    report = _seed_report(db_session)
    db_session.add(
        Subscription(email="c@d.com", frequencies='["daily"]', confirmed=True, confirm_token="t1", unsubscribe_token="t2")
    )
    db_session.commit()
    result = deliver_report_email(db_session, report)
    assert result == {"sent": 0, "skipped": 1, "failed": 0, "targets": 1}
    log = db_session.query(DeliveryLog).one()
    assert log.status == "skipped"


def test_delivery_webhook_skipped_without_config(db_session):
    from app.delivery.webhook import deliver_report_webhooks

    report = _seed_report(db_session)
    result = deliver_report_webhooks(db_session, report)
    assert result == {"wecom": "skipped", "telegram": "skipped"}
