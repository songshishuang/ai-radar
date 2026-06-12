# AI 情报站（AI Intel Site）设计文档

- 日期：2026-06-12
- 状态：已获用户批准（对话中三块设计逐块确认）
- 作者：Claude + songshishuang

## 1. 概述

个人自用的 AI 信息聚合与研报系统。自动抓取国外核心 AI 信息源，用 Claude API 生成中文摘要、分类与 PM 视角深度分析，产出日报/周报/月报，通过网站、邮件、RSS、微信/IM 四渠道订阅分发。

**目标用户**：产品经理本人（个人自用），订阅系统保留对外能力以备未来开放给团队。

**核心价值**：把分散的英文 AI 信息流转化为每天 10 分钟可读完的中文深度研报，覆盖四大内容类别：

1. 产研 AI 范式（提升产研效率的工具与方法论）
2. AI 技术（模型、论文、技术博客）
3. 社区开源项目
4. 行业最新 AI 产品

## 2. 需求确认记录

| 决策点 | 结论 |
|---|---|
| 使用范围 | 个人自用 |
| 接收方式 | 邮件 + 网站在线浏览 + RSS + 微信/IM 推送（全选） |
| 内容加工深度 | 深度研报模式（摘要 + 分类 + 重要度 + 每日重点深度分析） |
| 运行环境 | 自有 VPS / 云服务器 |
| LLM | Claude API（Haiku 批量摘要 / Sonnet 深度分析） |
| 数据源 | 核心厂商官方源 + 社区开源 + 行业媒体/Newsletter + Twitter/X 关键人物（全选） |
| 技术方案 | 方案 B：全栈 Web 应用（FastAPI + Next.js + PostgreSQL） |

## 3. 总体架构

VPS 上 Docker Compose 编排 5 个容器：

```
                    ┌─────────────── VPS (Docker Compose) ───────────────┐
  访客/用户 ─HTTPS─▶│ Caddy 反代 ──┬─▶ Next.js 前端（网站页面，SSR）      │
                    │              └─▶ FastAPI 后端 ◀──── RSSHub（兜底源）│
                    │                    ├─ REST API（内容/报告/订阅）    │
                    │                    ├─ APScheduler 定时管道          │
                    │                    └─ Claude API（摘要/深度分析）   │
                    │              PostgreSQL（内容/报告/订阅/日志）       │
                    └────────────────────────────────────────────────────┘
                         │ SMTP 邮件    │ 企微/TG webhook    │ RSS XML
```

**技术栈**

- 后端：Python 3.12 + FastAPI + SQLAlchemy + APScheduler + httpx + feedparser + anthropic SDK
- 前端：Next.js（App Router）+ Tailwind CSS，SSR
- 数据库：PostgreSQL 16（含全文搜索 FTS）
- 反代：Caddy（自动 HTTPS）
- 兜底抓取：RSSHub 自部署实例（仅用于 Twitter/X 等无 RSS 的源）

**容器**：`caddy` / `web`（Next.js）/ `api`（FastAPI，内含调度器）/ `db`（PostgreSQL）/ `rsshub`

## 4. 数据源清单（首批约 25 个，管理后台可增减）

| 类别 | 源 | 抓取方式 |
|---|---|---|
| 核心厂商 | OpenAI Blog/News、Anthropic News/Engineering、Google DeepMind Blog、Meta AI Blog、xAI News、Mistral News、Microsoft AI Blog、HuggingFace Blog | 官方 RSS/Atom |
| 产研AI范式 | Cursor Blog/Changelog、GitHub Blog (Copilot)、Claude Code Changelog、Vercel AI Blog、LangChain Blog | RSS + 网页抓取 |
| 社区开源 | Hacker News（Algolia API，AI 关键词且 ≥100 分）、GitHub Trending（AI 关键词过滤）、HuggingFace Daily Papers / Trending Models、Reddit r/LocalLLaMA 等 | 公开 API / JSON |
| 行业媒体 | TechCrunch AI、The Verge AI、VentureBeat AI、Ben's Bites、Product Hunt AI 榜 | RSS |
| Twitter/X | Sam Altman、Andrej Karpathy、各厂商官号 | RSSHub 路由，失败自动跳过并在日报标注 |

**源容错**：每源独立超时与重试；连续失败 3 次标记 degraded，日报尾部提示；单源故障不影响整体管道。

## 5. 数据模型（PostgreSQL）

- `sources` — 源配置：name, category, url, fetch_method(rss/api/scrape/rsshub), schedule, enabled, fail_count, status
- `items` — 内容条目：source_id, title, url(规范化唯一), author, published_at, raw_content, content_hash, created_at
- `enrichments` — AI 加工结果：item_id, summary_zh, category(四大类), tags[], importance_score(1-10), model, tokens_in/out, cost_usd
- `reports` — 报告：type(daily/weekly/monthly), period_date, markdown, html, headline_analysis(深度研报 JSON), stats
- `subscriptions` — 订阅：email, frequencies[](daily/weekly/monthly), confirmed, confirm_token, unsubscribe_token, created_at
- `delivery_logs` — 分发日志：report_id, channel(email/wecom/telegram), target, status, retries, error
- `pipeline_runs` — 管道运行日志：stage, started_at, finished_at, status, detail

## 6. AI 处理管道（四级流水线）

```
抓取入库 → ① 去重 → ② 批量摘要(Haiku) → ③ 每日深度分析(Sonnet) → ④ 周/月趋势提炼(Sonnet)
```

1. **去重**：URL 规范化 + 内容 hash + 标题相似度；同一事件多源报道合并为一条，保留全部来源链接。
2. **批量摘要 — Claude Haiku**（`claude-haiku-4-5-20251001`）：每条生成中文摘要（80-150 字）、四大类归类、标签、重要度评分 1-10。
3. **每日深度分析 — Claude Sonnet**（`claude-sonnet-4-6`）：当日重要度 ≥7 的 Top 3-5 条，每条生成 PM 视角研报：事件背景 → 产业影响 → 竞品对位 → 对产研效率的启示 → 建议关注的行动点。
4. **周/月提炼 — Claude Sonnet**：周报四维综述（本周大事/技术趋势/开源热点/产品动向）；月报月度综述 + 趋势研判 + 下月关注方向。

**成本**：日均 80-150 条，预计每月 $10-20。全部调用记录 token 与美元成本入库，后台展示成本曲线。

## 7. 报告设计

**日报**（每日北京时间 07:00，覆盖美国全天动态）

- 🔥 今日头条：Top 3-5 深度研报（PM 视角）
- 📋 分类速览：四大类逐条「中文摘要 + 原文链接 + 重要度标记」
- 📊 管道状态：抓取条数、异常源提示

**周报**（周一 07:30）：本周大事记 + 四维趋势综述 + 本周高分条目 Top 10

**月报**（每月 1 日 08:00）：月度综述 + 趋势研判 + 厂商动态时间线 + 下月关注方向

**降级规则**：摘要失败的条目以「原文标题 + 链接」形式进报告，不静默丢失；深度分析失败则当日头条降级为高分条目清单。

## 8. 网站与 API

### 页面（Next.js SSR）

| 页面 | 功能 |
|---|---|
| `/` | 最新日报全文 + 近期报告入口 |
| `/reports` | 日/周/月 + 日历浏览历史报告 |
| `/feed` | 全部条目流，按类别/标签/来源/重要度筛选 |
| `/search` | Postgres FTS 全文搜索（标题 + 摘要） |
| `/subscribe` | 邮箱 + 频率（日/周/月多选）订阅，确认邮件双重验证 |
| `/admin` | Token 登录：源管理、手动触发抓取、订阅管理、成本看板、管道日志 |

### API（FastAPI）

- `GET /api/reports?type=&date=` — 报告查询
- `GET /api/items?category=&tag=&source=&q=&min_score=` — 条目查询/搜索
- `POST /api/subscriptions` — 发起订阅（触发确认邮件）
- `GET /api/subscriptions/confirm?token=` / `GET /api/subscriptions/unsubscribe?token=` — 确认/退订
- `GET /rss/daily.xml` `/rss/weekly.xml` `/rss/monthly.xml` `/rss/feed.xml` — RSS 输出
- `POST /api/admin/*` — 管理操作（Bearer Token 认证）

## 9. 订阅与分发

- **邮件**：SMTP（Gmail 应用密码或 Resend），HTML 模板与网页同构，按订阅频率发送，底部退订链接
- **RSS**：报告流 3 路 + 全量条目流 1 路
- **微信/IM**：企业微信群机器人 + Telegram Bot 双通道 webhook，推送「头条标题 + 摘要 + 网站链接」
- 分发失败重试 2 次，写 `delivery_logs`，后台可见

## 10. 调度（APScheduler，时区 Asia/Shanghai）

| 任务 | 频率 |
|---|---|
| 抓取全部源 | 每 2 小时 |
| 摘要处理 | 每轮抓取后即时 |
| 日报生成 + 分发 | 每日 07:00 |
| 周报生成 + 分发 | 周一 07:30 |
| 月报生成 + 分发 | 每月 1 日 08:00 |

## 11. 错误处理与可观测性

- 源级隔离：单源 try/catch + 独立超时；连续失败 3 次降级
- Claude API：指数退避重试 3 次，失败走第 7 节降级规则
- 分发：失败重试 2 次 + 日志
- 管道每步写 `pipeline_runs`；可选 healthchecks.io 心跳告警

## 12. 测试策略

- pytest 单测：各源解析器（本地 fixture 样本）、去重逻辑、报告组装、订阅确认/退订流程
- Claude 调用全部 mock，测试零 API 成本
- E2E 冒烟：staging 模式限 5 条跑通「抓取→摘要→报告→分发」全链路

## 13. 非目标（YAGNI）

- 用户注册/登录体系（订阅仅凭邮箱 + 确认链接）
- 多租户、付费墙、评论互动
- 移动端 App（响应式网页覆盖移动浏览）
- 中文信息源（首期不做，架构上仅是加源配置）
