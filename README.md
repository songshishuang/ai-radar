# AI 情报站

个人 AI 信息聚合与研报系统：自动抓取国外核心 AI 信息源 → Claude 生成中文摘要与 PM 视角深度研报 → 日报/周报/月报 → 网站 / 邮件 / RSS / 企微·TG 订阅分发。

🌐 **在线站点（GitHub Pages）**：https://songshishuang.github.io/ai-radar/
🧰 **配套 Skill**：[ai-radar](https://github.com/songshishuang/ai-radar-skill) — 在 Claude Code / agent 工具里一句话生成 AI 研报（零部署版，本项目的 skill 形态产物）

- 设计文档：[docs/superpowers/specs/2026-06-12-ai-intel-site-design.md](docs/superpowers/specs/2026-06-12-ai-intel-site-design.md)
- 实施计划：[docs/superpowers/plans/2026-06-12-ai-intel-site.md](docs/superpowers/plans/2026-06-12-ai-intel-site.md)

## GitHub Pages 部署（A2：本地生成 + 静态托管，零服务器零 API key）

网站是 Next.js **静态导出**，托管在 GitHub Pages；报告由你本机用 claude CLI 生成，一条命令发布：

```bash
./publish.sh --gen   # 本地跑全量管道（抓取→加工→生成日/周/月报）→ 导出静态数据 → commit → push
./publish.sh         # 仅把已生成的报告重新导出并发布（不重跑管道）
```

`git push` 后 `.github/workflows/deploy.yml` 自动构建静态站并部署到 Pages。数据流：

| 动态全栈（VPS 版） | GitHub 静态版 |
|---|---|
| APScheduler 常驻调度 | 本机 `publish.sh` 触发生成 |
| FastAPI `/api` 运行时取数 | `backend/export_static.py` 导出 `frontend/content/*.json`（git 即数据库） |
| Next.js SSR | Next.js 静态导出（`output: export`，`PAGES_BASE_PATH=/ai-radar`） |
| 站内邮箱订阅表单 | 降级为 RSS 订阅页（`/rss/*.xml`，静态生成） |

> 邮件 / 企微 / TG 推送仍由下方「VPS 部署」的完整后端提供；GitHub 静态站提供网页浏览 + RSS。

## 本地运行（开发模式：SQLite + claude CLI）

前提：Python 3.12+、Node 20+、已登录的 [claude CLI](https://claude.com/claude-code)（LLM 走本机订阅，无需 API key）。

```bash
# 1. 后端
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt email-validator
.venv/bin/uvicorn app.api.main:app --port 8000   # 启动即建库+种子26源+调度器

# 2. 前端（另开终端）
cd frontend
npm install && npm run dev                        # http://localhost:3000

# 3. 手动触发一轮管道（默认 admin token 为 changeme）
curl -X POST -H "Authorization: Bearer changeme" localhost:8000/api/admin/run/ingest
curl -X POST -H "Authorization: Bearer changeme" localhost:8000/api/admin/run/enrich
curl -X POST -H "Authorization: Bearer changeme" localhost:8000/api/admin/run/daily
curl -X POST -H "Authorization: Bearer changeme" localhost:8000/api/admin/run/weekly
```

测试：`cd backend && .venv/bin/python -m pytest tests/ -v`（LLM 全部 mock，零成本）

## VPS 部署（生产模式：Postgres + Anthropic API + Docker Compose）

```bash
git clone <repo> && cd report/deploy
cp .env.example .env && vim .env     # 填 POSTGRES_PASSWORD / ANTHROPIC_API_KEY / ADMIN_TOKEN / 域名
vim Caddyfile                        # :80 改成你的域名即自动 HTTPS
docker compose up -d --build
```

五容器：`caddy`（反代+HTTPS）/ `web`（Next.js）/ `api`（FastAPI+调度）/ `db`（Postgres16）/ `rsshub`（Twitter 等无 RSS 源兜底）。

部署后把 Twitter 源 URL 改为 `http://rsshub:1200/twitter/user/<name>` 并启用（默认本地禁用）。

## 配置项（环境变量，前缀 INTEL_）

| 变量 | 默认 | 说明 |
|---|---|---|
| INTEL_DB_URL | sqlite:///data/intel.db | 数据库连接串 |
| INTEL_LLM_PROVIDER | claude-cli | claude-cli / anthropic-api / mock |
| INTEL_LLM_FAST_MODEL | claude-haiku-4-5-20251001 | 批量摘要模型 |
| INTEL_LLM_DEEP_MODEL | claude-sonnet-4-6 | 深度研报模型 |
| INTEL_ADMIN_TOKEN | changeme | /api/admin/* Bearer 认证 |
| INTEL_SMTP_* / INTEL_MAIL_FROM | 空 | 不配则邮件分发记 skipped |
| INTEL_WECOM_WEBHOOK_URL | 空 | 企微群机器人 |
| INTEL_TELEGRAM_BOT_TOKEN/CHAT_ID | 空 | TG 推送 |

## 调度（Asia/Shanghai）

| 任务 | 时间 |
|---|---|
| 抓取 + 摘要 | 每 2 小时 |
| 日报生成+分发 | 每日 07:00 |
| 周报 | 周一 07:30 |
| 月报 | 每月 1 日 08:00 |

## 订阅与输出

- 网站：`/`（最新日报）`/reports`（归档）`/feed`（条目流）`/search` `/subscribe`
- RSS：`/rss/daily.xml` `/rss/weekly.xml` `/rss/monthly.xml` `/rss/feed.xml`
- 报告 Markdown 同步落盘 `data/reports/`

## 源管理

26 个首批源见 `backend/app/seeds.py`（核心厂商 8 / 产研范式 5 / 社区开源 6 / 行业媒体 5 / X 2）。单源连续失败 3 次自动降级并在日报「管道状态」节标注，不影响整体。
