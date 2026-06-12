import json

from app.llm import MockProvider
from app.models import Enrichment, Item, Source
from app.pipeline.enrich import run_enrich


def _seed_items(db_session, n=2):
    s = Source(name="src", category="vendor", url="http://s", fetch_method="rss")
    db_session.add(s)
    db_session.flush()
    items = []
    for i in range(n):
        it = Item(source_id=s.id, title=f"Title {i}", url=f"https://x.com/{i}", content_hash=f"h{i}")
        db_session.add(it)
        items.append(it)
    db_session.commit()
    return items


def test_run_enrich_creates_enrichments(db_session):
    items = _seed_items(db_session, 2)
    resp = json.dumps(
        [
            {"id": items[0].id, "summary_zh": "摘要一", "category": "tech", "tags": ["LLM"], "importance": 8},
            {"id": items[1].id, "summary_zh": "摘要二", "category": "badcat", "tags": [], "importance": 99},
        ]
    )
    p = MockProvider(responses=[resp])
    detail = run_enrich(db_session, provider=p)
    assert detail["enriched"] == 2
    enr = {e.item_id: e for e in db_session.query(Enrichment).all()}
    assert enr[items[0].id].summary_zh == "摘要一"
    assert enr[items[1].id].category == "tech"  # 非法分类归 tech
    assert enr[items[1].id].importance_score == 10  # clamp 到 10


def test_run_enrich_skips_already_enriched(db_session):
    items = _seed_items(db_session, 1)
    p1 = MockProvider(responses=[json.dumps([{"id": items[0].id, "summary_zh": "x", "category": "tech", "tags": [], "importance": 5}])])
    run_enrich(db_session, provider=p1)
    p2 = MockProvider(responses=[])  # 无 pending → 不应调用 LLM
    detail = run_enrich(db_session, provider=p2)
    assert detail["pending"] == 0
    assert len(p2.calls) == 0


def test_run_enrich_bad_json_does_not_crash(db_session):
    _seed_items(db_session, 1)
    p = MockProvider(responses=["garbage", "more garbage"])  # 两次都坏 → 批次失败但不抛
    detail = run_enrich(db_session, provider=p)
    assert detail["enriched"] == 0
    assert detail["failed_batches"] == 1
