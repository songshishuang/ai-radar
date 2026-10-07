"""把 ai-radar skill 生成的 Markdown 报告导入数据库，之后跑 ./publish.sh 即发布到在线站。

用法（仓库根目录）：
    backend/.venv/bin/python backend/import_skill_report.py ~/skills/ai-radar-skill/ai-radar-reports/daily-2026-10-08.md [更多文件 ...]

- 文件名须为 {daily|weekly|monthly}-{period}.md，period 即站点路由里的日期 / ISO 周 / 月。
- 标题取正文第一个「# 」标题；速览段（周报为大事记）写进 stats.tldr，供首页摘要使用。
- 与管道生成的报告走同一套入库、HTML 渲染与 data/reports/ 归档；同一 type + period 已存在则覆盖。
- 只入库不发布。发布前先确认报告已通过 skill 的出处校验（verify_report.py）。
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db import SessionLocal, init_db  # noqa: E402
from app.models import Report  # noqa: E402
from app.pipeline.reports import _persist  # noqa: E402

_NAME_RE = re.compile(r"^(daily|weekly|monthly)-(\d{4}-\d{2}-\d{2}|\d{4}-W\d{2}|\d{4}-\d{2})\.md$")
_TLDR_HEADINGS = ("速览", "大事记")


def _plain(text: str) -> str:
    """去掉链接与强调标记，首页摘要按纯文本展示。"""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"\*\*|__|`", "", text)


def _tldr(markdown_text: str) -> str | None:
    lines, grab = [], False
    for line in markdown_text.splitlines():
        if line.startswith("## "):
            if grab:
                break
            grab = any(h in line for h in _TLDR_HEADINGS)
        elif grab and line.strip():
            lines.append(line.strip())
    return _plain(" ".join(lines)) or None


def parse_skill_report(path: Path) -> dict:
    m = _NAME_RE.match(path.name)
    if not m:
        raise ValueError(f"文件名须为 {{daily|weekly|monthly}}-{{period}}.md：{path.name}")
    markdown_text = path.read_text(encoding="utf-8")
    title = next((line[2:].strip() for line in markdown_text.splitlines() if line.startswith("# ")), None)
    if not title:
        raise ValueError(f"缺少一级标题：{path.name}")
    return {"type": m.group(1), "period": m.group(2), "title": title, "markdown": markdown_text, "tldr": _tldr(markdown_text)}


def import_report(session, rep: dict, source_file: str) -> Report:
    stats = {"source": "manual-ai-radar-skill", "source_file": source_file, "imported_at": datetime.now(timezone.utc).isoformat()}
    if rep["tldr"]:
        stats["tldr"] = rep["tldr"]
    return _persist(session, rep["type"], rep["period"], rep["title"], rep["markdown"], [], stats)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="把 ai-radar skill 的报告导入数据库")
    ap.add_argument("reports", nargs="+", help="skill 生成的报告 Markdown")
    args = ap.parse_args(argv)
    paths = [Path(p).expanduser() for p in args.reports]
    try:
        parsed = [parse_skill_report(p) for p in paths]  # 先全部校验，避免只导入一半
    except (OSError, ValueError) as e:
        print(f"导入失败：{e}", file=sys.stderr)
        return 2
    init_db()
    with SessionLocal() as session:
        for path, rep in zip(paths, parsed):
            report = import_report(session, rep, path.name)
            print(f"✓ {report.type}-{report.period_date}：{report.title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
