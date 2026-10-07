import json

import pytest
from sqlalchemy import select

import import_skill_report as isr
from app.models import Report
from app.pipeline import reports as reports_module

SAMPLE = """# AI 情报日报 · 2026-10-08

_☕ 正文约 2 分钟读完_

## ⚡ 今日速览

**OpenAI** 发布 [新模型](https://openai.com/x)，`Agents API` 公测。
第二句结论。

## 🔥 今日必读

**1. [事件 A](https://ex.com/a)** `9/10` · 3 源 · 官方
"""


@pytest.fixture()
def reports_dir(tmp_path, monkeypatch):
    out = tmp_path / "reports"
    monkeypatch.setattr(reports_module, "REPORTS_DIR", out)  # 不写进仓库的 data/reports/
    return out


def _write(tmp_path, name, text=SAMPLE):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_import_creates_report_with_tldr_and_archive(db_session, tmp_path, reports_dir):
    path = _write(tmp_path, "daily-2026-10-08.md")
    isr.import_report(db_session, isr.parse_skill_report(path), path.name)

    r = db_session.execute(select(Report)).scalar_one()
    assert (r.type, r.period_date, r.lens, r.title) == ("daily", "2026-10-08", "pm", "AI 情报日报 · 2026-10-08")
    assert r.markdown == SAMPLE and '<a href="https://ex.com/a">' in r.html
    stats = json.loads(r.stats)
    assert stats["source"] == "manual-ai-radar-skill" and stats["source_file"] == "daily-2026-10-08.md"
    assert stats["tldr"] == "OpenAI 发布 新模型，Agents API 公测。 第二句结论。"
    assert json.loads(r.headline_analysis) == []
    assert (reports_dir / "daily-2026-10-08.md").read_text(encoding="utf-8") == SAMPLE


def test_reimport_overwrites_same_period(db_session, tmp_path, reports_dir):
    path = _write(tmp_path, "daily-2026-10-08.md")
    isr.import_report(db_session, isr.parse_skill_report(path), path.name)
    path.write_text(SAMPLE.replace("2026-10-08\n", "2026-10-08（修订）\n", 1), encoding="utf-8")
    isr.import_report(db_session, isr.parse_skill_report(path), path.name)

    rows = db_session.execute(select(Report)).scalars().all()
    assert len(rows) == 1 and rows[0].title == "AI 情报日报 · 2026-10-08（修订）"


def test_weekly_uses_highlights_as_tldr(tmp_path):
    path = _write(tmp_path, "weekly-2026-W41.md", "# AI 情报周报 · 2026-W41\n\n## 🗓 本期大事记\n\n本周主轴。\n\n## 🔥 本期重大事件\n")
    rep = isr.parse_skill_report(path)
    assert (rep["type"], rep["period"], rep["tldr"]) == ("weekly", "2026-W41", "本周主轴。")


def test_rejects_bad_name_or_missing_title(tmp_path):
    with pytest.raises(ValueError):
        isr.parse_skill_report(_write(tmp_path, "report-2026-10-08.md"))
    with pytest.raises(ValueError):
        isr.parse_skill_report(_write(tmp_path, "daily-2026-10-09.md", "没有标题\n"))


def test_main_validates_all_files_before_touching_db(tmp_path, capsys):
    good = _write(tmp_path, "daily-2026-10-08.md")
    bad = _write(tmp_path, "notes.md")
    assert isr.main([str(good), str(bad)]) == 2
    assert "notes.md" in capsys.readouterr().err
