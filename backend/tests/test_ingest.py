from datetime import datetime, timezone

from app.fetchers import RawItem
from app.models import Item, PipelineRun, Source
from app.pipeline.ingest import content_hash_for, ingest_items, normalize_url, run_ingest
from app.seeds import SEED_SOURCES, seed_sources


def test_normalize_url_strips_tracking():
    assert normalize_url("https://a.com/p?utm_source=tw&id=1") == normalize_url("https://A.com/p/?id=1")
    assert normalize_url("https://a.com/p#frag") == normalize_url("https://a.com/p")


def test_content_hash_fallback_to_title():
    r = RawItem(title="no url item", url="")
    assert content_hash_for(r, "src") == content_hash_for(RawItem(title="no url item", url=""), "src")
    assert content_hash_for(r, "src") != content_hash_for(r, "other-src")


def test_ingest_items_dedup(db_session):
    s = Source(name="t", category="vendor", url="http://t", fetch_method="rss")
    db_session.add(s)
    db_session.flush()
    raw = [
        RawItem(title="A", url="https://x.com/a?utm_source=rss", published_at=datetime.now(timezone.utc)),
        RawItem(title="A dup", url="https://x.com/a"),  # 规范化后同 URL
        RawItem(title="B", url="https://x.com/b"),
    ]
    assert ingest_items(db_session, s, raw) == 2
    db_session.commit()
    assert db_session.query(Item).count() == 2
    # 第二轮全部跳过
    assert ingest_items(db_session, s, raw) == 0


def test_seed_sources_idempotent(db_session):
    n1 = seed_sources(db_session)
    n2 = seed_sources(db_session)
    assert n1 == len(SEED_SOURCES)
    assert n2 == 0


def test_run_ingest_isolates_failures(db_session, monkeypatch):
    ok = Source(name="ok-src", category="vendor", url="http://ok", fetch_method="rss")
    bad = Source(name="bad-src", category="vendor", url="http://bad", fetch_method="hackernews")
    rsshub = Source(name="x-src", category="twitter", url="rsshub://x", fetch_method="rsshub")
    db_session.add_all([ok, bad, rsshub])
    db_session.commit()

    def fake_rss(source):
        return [RawItem(title="hello", url="https://ok.com/1")]

    def fake_hn(source):
        raise RuntimeError("network down")

    monkeypatch.setitem(__import__("app.fetchers", fromlist=["FETCHERS"]).FETCHERS, "rss", fake_rss)
    monkeypatch.setitem(__import__("app.fetchers", fromlist=["FETCHERS"]).FETCHERS, "hackernews", fake_hn)

    detail = run_ingest(db_session)
    assert detail["new"] == 1
    assert any("bad-src" in f for f in detail["failed_sources"])
    assert "x-src" in detail["degraded_sources"]  # 未注册 fetcher → degraded
    assert db_session.query(PipelineRun).filter_by(stage="ingest", status="success").count() == 1
    # bad-src 连续失败 3 次 → degraded
    run_ingest(db_session)
    run_ingest(db_session)
    db_session.refresh(bad)
    assert bad.fail_count >= 3
    assert bad.status == "degraded"
