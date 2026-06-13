#!/usr/bin/env bash
# 本地发布流水线（A2 模式：本地生成 + GitHub Pages 托管）
#
#   ./publish.sh           # 仅导出已生成的报告为静态数据 → commit → push
#   ./publish.sh --gen     # 先跑全量管道（抓取→加工→生成日/周/月报）再导出发布
#
# push 后 GitHub Actions 自动构建 Next.js 静态站并部署到 Pages。
set -euo pipefail
cd "$(dirname "$0")"

SITE_BASE="${SITE_BASE:-https://songshishuang.github.io/ai-radar}"
PY=backend/.venv/bin/python

if [[ "${1:-}" == "--gen" ]]; then
  echo "▶ 跑全量管道（抓取 + 加工 + 生成报告）…"
  ( cd backend && .venv/bin/python -c "
from app.db import SessionLocal, init_db
from app.pipeline.ingest import run_ingest
from app.pipeline.enrich import run_enrich
from app.pipeline.reports import build_daily, build_weekly, build_monthly
init_db()
with SessionLocal() as s:
    print('ingest:', run_ingest(s))
    print('enrich:', run_enrich(s))
    build_daily(s); build_weekly(s); build_monthly(s)
    print('reports built')
" )
fi

echo "▶ 导出静态数据（content JSON + RSS）…"
( cd backend && SITE_BASE="$SITE_BASE" .venv/bin/python export_static.py )

echo "▶ 提交并推送…"
git add frontend/content frontend/public/rss data/reports 2>/dev/null || true
if git diff --cached --quiet; then
  echo "（无数据变更，跳过提交）"
else
  git commit -m "data: refresh reports $(date +%F-%H%M)"
fi
git push

echo "✅ 已推送。GitHub Actions 正在构建并部署 → https://songshishuang.github.io/ai-radar/"
