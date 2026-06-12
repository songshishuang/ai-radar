import json
from datetime import datetime, timedelta, timezone

from app.llm import MockProvider
from app.models import Enrichment, Item, Report, Source
from app.pipeline.reports import build_daily, build_weekly

DEEP_RESPONSE = json.dumps(
    {
        "headline": "重磅模型发布",
        "background": "背景",
        "industry_impact": "影响",
        "competitive": "竞品",
        "rd_efficiency": "提效启示",
        "biz_opportunity": "商业机会",
        "action_items": ["动作一", "动作二"],
    },
    ensure_ascii=False,
)

WEEKLY_RESPONSE = json.dumps(
    {
        "highlights": "本周大事记内容",
        "trends": {"paradigm": "范式趋势", "tech": "技术趋势", "opensource": "开源趋势", "product": "产品趋势"},
        "next_week_watch": ["关注一", "关注二"],
    },
    ensure_ascii=False,
)


def _seed_enriched(db_session, n=5, high_scores=2):
    s = Source(name="seed-src", category="vendor", url="http://s", fetch_method="rss")
    db_session.add(s)
    db_session.flush()
    now = datetime.now(timezone.utc)
    cats = ["model-release", "dev-tooling", "opensource", "business"]
    for i in range(n):
        it = Item(
            source_id=s.id,
            title=f"News {i}",
            url=f"https://n.com/{i}",
            content_hash=f"hh{i}",
            published_at=now - timedelta(hours=2 * i),
            raw_content=f"content {i}",
        )
        db_session.add(it)
        db_session.flush()
        db_session.add(
            Enrichment(
                item_id=it.id,
                summary_zh=f"中文摘要{i}",
                category=cats[i % 4],
                tags='["AI"]',
                importance_score=9 if i < high_scores else 5,
            )
        )
    db_session.commit()


def test_build_daily_pyramid_structure(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("app.pipeline.reports.REPORTS_DIR", tmp_path)
    _seed_enriched(db_session, n=5, high_scores=2)
    # 顺序：2 条 ≥8 深度分析 + 1 次 TL;DR
    p = MockProvider(responses=[DEEP_RESPONSE, DEEP_RESPONSE, "速览第一句。第二句。第三句。"])
    report = build_daily(db_session, date_str="2026-06-12", provider=p)
    assert report.type == "daily" and report.period_date == "2026-06-12"
    assert "⚡ 今日速览" in report.markdown
    assert "🔥 今日必读" in report.markdown
    assert "重磅模型发布" in report.markdown
    assert "本期共收录 **5**" in report.markdown
    assert "<h1" in report.html
    stats = json.loads(report.stats)
    assert stats["total"] == 5
    assert stats["tldr"].startswith("速览")
    assert (tmp_path / "daily-2026-06-12.md").exists()


def test_build_daily_upsert_same_date(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("app.pipeline.reports.REPORTS_DIR", tmp_path)
    _seed_enriched(db_session, n=2, high_scores=0)
    build_daily(db_session, date_str="2026-06-12", provider=MockProvider(responses=[]))
    build_daily(db_session, date_str="2026-06-12", provider=MockProvider(responses=[]))
    assert db_session.query(Report).filter_by(type="daily", period_date="2026-06-12").count() == 1


def test_build_daily_degrades_without_headlines(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("app.pipeline.reports.REPORTS_DIR", tmp_path)
    _seed_enriched(db_session, n=3, high_scores=1)
    p = MockProvider(responses=["bad", "bad"])  # 深度分析失败 → 降级高分清单
    report = build_daily(db_session, date_str="2026-06-13", provider=p)
    assert "今日高分条目" in report.markdown
    assert "本期共收录" in report.markdown


def test_build_weekly_structure(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("app.pipeline.reports.REPORTS_DIR", tmp_path)
    _seed_enriched(db_session, n=6, high_scores=2)
    p = MockProvider(responses=[WEEKLY_RESPONSE])
    report = build_weekly(db_session, provider=p)
    assert report.type == "weekly"
    assert "本周大事记" in report.markdown
    assert "四维趋势综述" in report.markdown
    assert "下周关注" in report.markdown
    assert "本周其他高分条目" in report.markdown
