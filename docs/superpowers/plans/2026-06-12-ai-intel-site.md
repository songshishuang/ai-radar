# AI 情报站实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建成 AI 信息聚合与研报系统（抓取 → Claude 管道 → 日/周/月报 → 网站/邮件/RSS/IM 分发），测试通过，并真实生成 2026-06-12 日报与本周（06-08~06-12）周报。

**Architecture:** FastAPI 后端（抓取管道 + LLM 管道 + REST API + 调度）+ Next.js 前端 + SQLAlchemy ORM（本地 SQLite / 生产 Postgres 同一套代码）。LLM 走 Provider 抽象：本地 `claude-cli`（subprocess 调 claude CLI，用订阅）、生产 `anthropic-api`、测试 `mock`。部署物（Docker Compose/Caddy）作为交付文件，本地不跑容器。

**Tech Stack:** Python 3.14 · FastAPI · SQLAlchemy 2.x · feedparser · httpx · pytest · Next.js 15 (App Router) · Tailwind CSS · claude CLI

**环境约束（本地）:** 无 Docker、无 Postgres、无 ANTHROPIC_API_KEY；有 claude CLI 2.1.141。Twitter/RSSHub 源置为 `enabled=false`，日报管道状态节如实标注。

---

## 文件地图

```
report/
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py            # Settings（env 驱动：DB_URL/LLM_PROVIDER/SMTP/webhook/ADMIN_TOKEN）
│   │   ├── db.py                # engine + SessionLocal + init_db
│   │   ├── models.py            # 7 表：Source/Item/Enrichment/Report/Subscription/DeliveryLog/PipelineRun
│   │   ├── llm.py               # LLMProvider 抽象 + AnthropicAPI/ClaudeCLI/Mock + complete_json
│   │   ├── seeds.py             # 26 个源种子数据
│   │   ├── fetchers/
│   │   │   ├── __init__.py      # FETCHERS 注册表 + RawItem dataclass + fetch_source 入口
│   │   │   ├── rss.py           # RSS/Atom 通用（feedparser）
│   │   │   ├── hackernews.py    # Algolia API，AI 关键词 ≥100 分
│   │   │   ├── github_trending.py  # trending 页面解析
│   │   │   ├── huggingface.py   # daily_papers + trending models API
│   │   │   └── reddit.py        # top.json
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py        # run_ingest：逐源抓取→规范化→去重→入库→fail_count 管理
│   │   │   ├── enrich.py        # run_enrich：批量 Haiku 摘要/分类/标签/评分
│   │   │   ├── analyze.py       # deep_analyze：Sonnet PM 视角研报（Top3-5）
│   │   │   └── reports.py       # build_daily/build_weekly/build_monthly → Markdown+HTML 入库
│   │   ├── delivery/
│   │   │   ├── __init__.py
│   │   │   ├── email.py         # SMTP 发送（HTML），confirm/unsubscribe 邮件
│   │   │   └── webhook.py       # 企微/Telegram 卡片推送
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── main.py          # FastAPI app：/api/reports /api/items /api/subscriptions /rss/*.xml /api/admin/*
│   │   └── scheduler.py         # APScheduler：抓取 2h / 日报 07:00 / 周报周一 07:30 / 月报 1 日 08:00
│   └── tests/
│       ├── conftest.py          # 内存 SQLite + MockLLM fixture
│       ├── fixtures/sample_rss.xml · sample_hn.json · sample_reddit.json · sample_hf_papers.json
│       ├── test_models.py  test_llm.py  test_fetchers.py  test_ingest.py
│       ├── test_enrich.py  test_reports.py  test_api.py
├── frontend/
│   ├── package.json  next.config.mjs  tailwind.config.ts  app/globals.css
│   ├── lib/api.ts               # 后端 API 客户端（fetch 封装，NEXT_PUBLIC_API_BASE）
│   └── app/
│       ├── layout.tsx           # 导航：首页/报告/信息流/搜索/订阅
│       ├── page.tsx             # 首页=最新日报渲染
│       ├── reports/page.tsx     # 归档列表（type+日期）
│       ├── reports/[type]/[date]/page.tsx  # 报告详情（渲染存库 HTML）
│       ├── feed/page.tsx        # 条目流（分类/来源/评分筛选）
│       ├── search/page.tsx      # 搜索
│       └── subscribe/page.tsx   # 订阅表单（POST /api/subscriptions）
├── deploy/
│   ├── docker-compose.yml       # caddy/web/api/db/rsshub 五容器
│   ├── Dockerfile.api  Dockerfile.web  Caddyfile  .env.example
├── data/                        # 本地 SQLite + 生成的报告 markdown 落盘（gitignore db）
└── README.md                    # 本地运行 + VPS 部署手册
```

**报告时间窗口规则：** 日报(D) = 自上一份日报以来的新条目（无上一份则回溯 36h）；周报 = 本周一 00:00 (Asia/Shanghai) 至生成时刻；月报 = 当月 1 日 00:00 至生成时刻。

---

### Task 1: 后端骨架 + 数据模型

**Files:**
- Create: `backend/requirements.txt`, `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/db.py`, `backend/app/models.py`, `backend/tests/conftest.py`, `backend/tests/test_models.py`, `.gitignore`

- [ ] **Step 1.1: requirements.txt 并安装**

```
fastapi
uvicorn[standard]
sqlalchemy>=2.0
feedparser
httpx
apscheduler
jinja2
pydantic-settings
anthropic
pytest
pytest-asyncio
beautifulsoup4
markdown
```

Run: `cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
Expected: 全部安装成功（Python 3.14 如有包不兼容，记录并以兼容版本号固定）

- [ ] **Step 1.2: config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_url: str = "sqlite:///../data/intel.db"
    llm_provider: str = "claude-cli"        # claude-cli | anthropic-api | mock
    llm_fast_model: str = "claude-haiku-4-5-20251001"
    llm_deep_model: str = "claude-sonnet-4-6"
    anthropic_api_key: str = ""
    admin_token: str = "changeme"
    site_base_url: str = "http://localhost:3000"
    smtp_host: str = ""; smtp_port: int = 587
    smtp_user: str = ""; smtp_password: str = ""
    mail_from: str = ""
    wecom_webhook_url: str = ""; telegram_bot_token: str = ""; telegram_chat_id: str = ""
    timezone: str = "Asia/Shanghai"
    model_config = {"env_file": ".env", "env_prefix": "INTEL_"}

settings = Settings()
```

- [ ] **Step 1.3: 写失败测试 test_models.py**（核心断言：7 表可建、Item 按 content_hash 唯一、Report (type,period_date) 唯一）

```python
def test_tables_create(db_session):
    from app import models
    names = {t.name for t in models.Base.metadata.sorted_tables}
    assert {"sources","items","enrichments","reports","subscriptions","delivery_logs","pipeline_runs"} <= names

def test_item_unique_hash(db_session):
    from app.models import Source, Item
    s = Source(name="x", category="vendor", url="http://a", fetch_method="rss")
    db_session.add(s); db_session.flush()
    db_session.add(Item(source_id=s.id, title="t", url="http://a/1", content_hash="h1"))
    db_session.flush()
    import pytest, sqlalchemy.exc
    db_session.add(Item(source_id=s.id, title="t2", url="http://a/2", content_hash="h1"))
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        db_session.flush()
```

- [ ] **Step 1.4: 实现 db.py + models.py 使测试通过**

models.py 关键定义（列完整，后续任务直接引用这些字段名）：

```python
class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]; category: Mapped[str]   # vendor|paradigm|community|media|twitter
    url: Mapped[str]
    fetch_method: Mapped[str]                  # rss|hackernews|github_trending|hf_papers|hf_models|reddit|rsshub
    enabled: Mapped[bool] = mapped_column(default=True)
    fail_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="ok")   # ok|degraded
    last_fetched_at: Mapped[datetime | None]

class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    title: Mapped[str]; url: Mapped[str]
    author: Mapped[str] = mapped_column(default="")
    published_at: Mapped[datetime | None]
    raw_content: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str] = mapped_column(unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

class Enrichment(Base):
    __tablename__ = "enrichments"
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), unique=True)
    summary_zh: Mapped[str] = mapped_column(Text)
    category: Mapped[str]      # paradigm|tech|opensource|product
    tags: Mapped[str]          # JSON list 序列化
    importance_score: Mapped[int]
    model: Mapped[str]; tokens_in: Mapped[int] = mapped_column(default=0)
    tokens_out: Mapped[int] = mapped_column(default=0)
    cost_usd: Mapped[float] = mapped_column(default=0.0)

class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("type", "period_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]          # daily|weekly|monthly
    period_date: Mapped[str]   # daily: 2026-06-12 / weekly: 2026-W24 / monthly: 2026-06
    title: Mapped[str]
    markdown: Mapped[str] = mapped_column(Text)
    html: Mapped[str] = mapped_column(Text)
    headline_analysis: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    stats: Mapped[str] = mapped_column(Text, default="{}")              # JSON
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    frequencies: Mapped[str] = mapped_column(default='["daily"]')  # JSON list
    confirmed: Mapped[bool] = mapped_column(default=False)
    confirm_token: Mapped[str]; unsubscribe_token: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

class DeliveryLog(Base):
    __tablename__ = "delivery_logs"
    id; report_id: FK reports.id; channel: str; target: str
    status: str = "pending"; retries: int = 0; error: str = ""
    created_at: datetime

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    id; stage: str; started_at: datetime; finished_at: datetime|None
    status: str = "running"   # running|success|failed
    detail: str = "{}"        # JSON：抓了几条/几源失败/token 用量
```

conftest.py：`db_session` fixture 用 `sqlite://`（内存）建全部表，每测试回滚。

Run: `cd backend && .venv/bin/python -m pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 1.5: Commit** `feat(backend): skeleton + data models`

### Task 2: LLM Provider 抽象

**Files:**
- Create: `backend/app/llm.py`, `backend/tests/test_llm.py`

- [ ] **Step 2.1: 失败测试**（Mock provider 返回预置 JSON；complete_json 能解析 ```json 包裹和裸 JSON；解析失败抛 LLMError）

```python
def test_mock_complete_json():
    from app.llm import MockProvider, complete_json
    p = MockProvider(responses=['```json\n[{"id": 1, "summary_zh": "测试"}]\n```'])
    out = complete_json(p, "prompt", tier="fast")
    assert out[0]["summary_zh"] == "测试"

def test_claude_cli_command_shape(monkeypatch):
    from app.llm import ClaudeCLIProvider
    captured = {}
    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        class R: returncode=0; stdout='{"ok":true}'; stderr=""
        return R()
    monkeypatch.setattr("subprocess.run", fake_run)
    p = ClaudeCLIProvider()
    p.complete("hello", tier="deep")
    assert "--model" in captured["cmd"]
```

- [ ] **Step 2.2: 实现 llm.py**

接口（后续管道统一用这两个函数）：

```python
class LLMProvider(Protocol):
    def complete(self, prompt: str, tier: str = "fast") -> str: ...

class ClaudeCLIProvider:
    """subprocess 调 claude CLI：claude -p --model <m> --max-turns 1，prompt 走 stdin"""
    def complete(self, prompt, tier="fast"):
        model = settings.llm_fast_model if tier == "fast" else settings.llm_deep_model
        cmd = ["claude", "-p", "--model", model, "--max-turns", "1",
               "--permission-mode", "dontAsk", "--no-cache"]
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=600)
        if r.returncode != 0: raise LLMError(r.stderr[:500])
        return r.stdout.strip()

class AnthropicAPIProvider:  # anthropic SDK messages.create，max_tokens 8192
class MockProvider:          # 顺序弹出预置 responses

def get_provider() -> LLMProvider   # 按 settings.llm_provider 工厂
def complete_json(provider, prompt, tier) -> Any
    # strip ```json fence → json.loads → 失败重试 1 次（重试时在 prompt 尾部追加“只输出合法 JSON”）→ 再失败抛 LLMError
```

注意：claude CLI 实际可用 flag 以 `claude --help` 实测为准，在本步实测并修正（如 `--no-cache`/`--permission-mode` 不存在则移除；`--max-turns 1` 保留防工具调用）。

Run: `pytest tests/test_llm.py -v` Expected: PASS

- [ ] **Step 2.3: claude-cli 冒烟实测**

Run: `echo '回复 JSON：{"ping":"pong"}，只输出 JSON' | claude -p --model claude-haiku-4-5-20251001 --max-turns 1`
Expected: 输出含 `{"ping":"pong"}`（验证订阅通道可用；如模型名不被 CLI 接受则改用 CLI 支持的别名 `haiku`/`sonnet` 并回写 config 默认值）

- [ ] **Step 2.4: Commit** `feat(backend): LLM provider abstraction (claude-cli/api/mock)`

### Task 3: Fetcher 框架 + 全部抓取器

**Files:**
- Create: `backend/app/fetchers/__init__.py`, `rss.py`, `hackernews.py`, `github_trending.py`, `huggingface.py`, `reddit.py`, `backend/tests/test_fetchers.py`, `backend/tests/fixtures/*`

- [ ] **Step 3.1: 失败测试**（每个 fetcher 对本地 fixture 解析出正确字段；无网络）

```python
def test_rss_parse(fixtures):
    from app.fetchers.rss import parse_feed
    items = parse_feed((fixtures / "sample_rss.xml").read_text(), source_url="https://x.com/feed")
    assert items[0].title and items[0].url and items[0].published_at

def test_hn_parse(fixtures):
    from app.fetchers.hackernews import parse_response
    items = parse_response(json.loads((fixtures / "sample_hn.json").read_text()))
    assert all(i.extra.get("points", 0) >= 100 for i in items)
```

fixtures：手写最小样本（RSS 2 条、HN hits 2 条、reddit children 2 条、HF papers 2 条）。

- [ ] **Step 3.2: 实现框架**

```python
@dataclass
class RawItem:
    title: str; url: str
    author: str = ""; published_at: datetime | None = None
    content: str = ""; extra: dict = field(default_factory=dict)

# fetchers/__init__.py
FETCHERS: dict[str, Callable[[Source], list[RawItem]]] = {
    "rss": fetch_rss, "hackernews": fetch_hackernews,
    "github_trending": fetch_github_trending,
    "hf_papers": fetch_hf_papers, "hf_models": fetch_hf_models,
    "reddit": fetch_reddit,
}   # "rsshub" 不注册 → ingest 对未知方法记 degraded
```

各 fetcher 要点：
- `rss.py`: feedparser.parse(httpx GET text)；`parse_feed(text, source_url)` 纯函数便于测试；published 缺失用 updated；content 取 summary/content[0].value 去 HTML 标签（BeautifulSoup get_text）截断 3000 字。
- `hackernews.py`: GET `https://hn.algolia.com/api/v1/search_by_date?tags=story&numericFilters=points>100,created_at_i>{36h前}&query={kw}`，kw 循环 ["AI","LLM","GPT","Claude","Gemini","agent","model"] 去重合并；`parse_response(json)` 纯函数。
- `github_trending.py`: GET `https://github.com/trending?since=daily` 解析 `article.Box-row`（h2 a→repo、p→desc、星数）；AI 过滤：desc/名称含 ai|llm|gpt|agent|model|rag|diffusion|transformer（不区分大小写）。
- `huggingface.py`: papers GET `https://huggingface.co/api/daily_papers?limit=20`；models GET `https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=15`。
- `reddit.py`: GET `{source.url}` (top.json?t=day&limit=25)，UA 头 `intel-bot/0.1`，score≥50 过滤。

统一：httpx timeout 20s，UA 默认 `Mozilla/5.0 (compatible; ai-intel-bot/0.1)`。

Run: `pytest tests/test_fetchers.py -v` Expected: PASS

- [ ] **Step 3.3: Commit** `feat(backend): fetcher framework + 6 fetchers`

### Task 4: Seeds + Ingest 管道（去重）

**Files:**
- Create: `backend/app/seeds.py`, `backend/app/pipeline/__init__.py`, `backend/app/pipeline/ingest.py`, `backend/tests/test_ingest.py`

- [ ] **Step 4.1: seeds.py — 26 源**

| category | name | fetch_method | url |
|---|---|---|---|
| vendor | OpenAI News | rss | https://openai.com/news/rss.xml |
| vendor | Anthropic News | rss | https://www.anthropic.com/rss.xml |
| vendor | Google DeepMind | rss | https://deepmind.google/blog/rss.xml |
| vendor | Google AI Blog | rss | https://blog.google/technology/ai/rss/ |
| vendor | Meta AI Blog | rss | https://ai.meta.com/blog/rss/ |
| vendor | Microsoft AI | rss | https://blogs.microsoft.com/ai/feed/ |
| vendor | HuggingFace Blog | rss | https://huggingface.co/blog/feed.xml |
| vendor | Mistral News | rss | https://mistral.ai/feed.xml |
| paradigm | Claude Code Releases | rss | https://github.com/anthropics/claude-code/releases.atom |
| paradigm | Cursor Changelog | rss | https://www.cursor.com/changelog/rss.xml |
| paradigm | GitHub Blog | rss | https://github.blog/feed/ |
| paradigm | Vercel Blog | rss | https://vercel.com/atom |
| paradigm | LangChain Blog | rss | https://blog.langchain.dev/rss/ |
| community | Hacker News AI | hackernews | https://hn.algolia.com/api/v1/search_by_date |
| community | GitHub Trending | github_trending | https://github.com/trending?since=daily |
| community | HF Daily Papers | hf_papers | https://huggingface.co/api/daily_papers |
| community | HF Trending Models | hf_models | https://huggingface.co/api/models |
| community | r/LocalLLaMA | reddit | https://www.reddit.com/r/LocalLLaMA/top.json?t=day&limit=25 |
| community | r/MachineLearning | reddit | https://www.reddit.com/r/MachineLearning/top.json?t=day&limit=25 |
| media | TechCrunch AI | rss | https://techcrunch.com/category/artificial-intelligence/feed/ |
| media | The Verge AI | rss | https://www.theverge.com/rss/ai-artificial-intelligence/index.xml |
| media | VentureBeat AI | rss | https://venturebeat.com/category/ai/feed/ |
| media | Ben's Bites | rss | https://bensbites.beehiiv.com/feed |
| media | Product Hunt | rss | https://www.producthunt.com/feed |
| twitter | X: @sama | rsshub | rsshub://twitter/user/sama (enabled=false 本地) |
| twitter | X: @karpathy | rsshub | rsshub://twitter/user/karpathy (enabled=false 本地) |

`seed_sources(session)`：按 (name) upsert，幂等。URL 实抓 404/403 时由 ingest 容错标 degraded（首跑后按实情修正 URL）。

- [ ] **Step 4.2: 失败测试 test_ingest.py**

```python
def test_dedup_by_url_normalization(db_session):
    # http://A?utm_source=x 与 http://A 视为同条
    from app.pipeline.ingest import normalize_url, content_hash_for
    assert normalize_url("https://a.com/p?utm_source=tw&id=1") == normalize_url("https://a.com/p?id=1")

def test_ingest_skips_existing(db_session, monkeypatch):
    # 同一 RawItem 跑两轮 ingest，items 只有 1 条；PipelineRun 记录 success
```

- [ ] **Step 4.3: 实现 ingest.py**

```python
def normalize_url(url):  # 去 utm_*/ref/fbclid 参数、去 fragment、去尾斜杠、host 小写
def content_hash_for(raw: RawItem) -> str:  # sha256(normalize_url(url))；url 为空用 sha256(title+source)
def run_ingest(session, only_source: str | None = None) -> dict:
    # 遍历 enabled sources：fetcher = FETCHERS.get(fetch_method)
    #   无 fetcher（rsshub）→ source.status="degraded"，跳过
    #   抓取异常 → fail_count += 1（≥3 置 degraded），continue；成功 → fail_count=0,status="ok"
    #   每条 RawItem → content_hash 查重 → 新条目入库
    # 写 PipelineRun(stage="ingest", detail={"fetched": n, "new": m, "failed_sources": [...]})
```

Run: `pytest tests/test_ingest.py -v` Expected: PASS

- [ ] **Step 4.4: Commit** `feat(backend): seeds + ingest pipeline with dedup`

### Task 5: Enrich 管道（Haiku 摘要/分类/评分）

**Files:**
- Create: `backend/app/pipeline/enrich.py`, `backend/tests/test_enrich.py`

- [ ] **Step 5.1: 失败测试**（MockProvider 喂 2 条 → 产生 2 条 Enrichment；LLM 坏 JSON → 重试后跳过该批不抛出；已 enrich 的不重复处理）

- [ ] **Step 5.2: 实现**

批处理 prompt 模板（BATCH_PROMPT，每批 ≤12 条）：

```
你是 AI 行业分析师。对下列 {n} 条英文 AI 资讯逐条输出 JSON。
分类 category 四选一：paradigm(产研AI范式/研发提效工具) | tech(模型与技术) |
opensource(开源项目) | product(行业AI产品/商业动态)。
importance 1-10：重大发布/范式变化 8-10；值得关注 5-7；一般 1-4。
对产品经理视角特别相关的（产研提效工具、商业机会信号）评分上浮 1 分。
输出格式（只输出 JSON 数组，无其他文字）：
[{"id": <原id>, "summary_zh": "<80-150字中文摘要>", "category": "...",
  "tags": ["...","..."], "importance": <int>}]
条目：
{id} | {title} | {source_name} | {content 截断400字}
...
```

```python
def run_enrich(session, batch_size=12) -> dict:
    # 查无 Enrichment 的 items → 分批 complete_json(provider, prompt, tier="fast")
    # 校验每条 id 对得上、category 合法（非法归 "tech"）、importance clamp 1-10
    # tags JSON 序列化存储；记录 PipelineRun(stage="enrich")
```

Run: `pytest tests/test_enrich.py -v` Expected: PASS

- [ ] **Step 5.3: Commit** `feat(backend): enrich pipeline (batch summarize/classify/score)`

### Task 6: 深度分析 + 报告组装

**Files:**
- Create: `backend/app/pipeline/analyze.py`, `backend/app/pipeline/reports.py`, `backend/tests/test_reports.py`

- [ ] **Step 6.1: 失败测试**（Mock 数据 5 条已 enrich → build_daily 产出 Report：markdown 含「今日头条」「分类速览」节、html 非空、stats JSON 含条数；同日重跑 upsert 不报错；build_weekly 聚合本周条目）

- [ ] **Step 6.2: 实现 analyze.py**

DEEP_PROMPT（tier="deep"，对 importance≥7 的 Top3-5 逐条）：

```
你是资深产品经理出身的 AI 行业分析师，为一位关注「产研提效」与「商业产品机会」的
PM 写深度解读。事件：{title}\n{summary_zh}\n原文要点：{content 截断1500字}
输出 JSON：{"headline": "<中文标题≤30字>",
 "background": "<事件背景 2-3 句>",
 "industry_impact": "<产业影响 2-3 句>",
 "competitive": "<竞品对位 2-3 句>",
 "rd_efficiency": "<对产研提效的启示，给到可落地动作>",
 "biz_opportunity": "<商业产品机会信号>",
 "action_items": ["<PM 本周可做的具体动作>", "..."]}
```

- [ ] **Step 6.3: 实现 reports.py**

```python
def items_for_daily(session, now) -> list:   # 自上份日报 created_at 起；无则 36h 回溯
def items_for_weekly(session, now) -> list:  # 本周一 00:00 CST 起 published/created
def build_daily(session, date_str) -> Report:
    # ① Top: importance≥7 取前5 → analyze.deep_analyze
    # ② 四分类分组（importance 降序，每类上限 15 条）
    # ③ stats: {"total": n, "by_category": {...}, "degraded_sources": [...], "tokens": ...}
    # ④ render markdown（结构：# 标题 / ## 🔥 今日头条(逐条五段) / ## 📋 分类速览(四节) / ## 📊 管道状态）
    # ⑤ html = markdown lib 渲染 + 内联简洁样式（jinja2 模板 report.html.j2）
    # ⑥ upsert Report(type="daily", period_date=date_str)，markdown 同步落盘 data/reports/daily-{date}.md
def build_weekly(session, week_str) -> Report:
    # 头部「本周大事」= 本周 importance≥8 全列；
    # 「四维趋势综述」= 把本周全部摘要按类目喂 Sonnet 出趋势(WEEKLY_PROMPT)；
    # 「高分 Top10」表格；stats 同上
WEEKLY_PROMPT 输出 JSON：{"highlights": "...", "trends": {"paradigm": "...",
 "tech": "...", "opensource": "...", "product": "..."},
 "next_week_watch": ["...建议关注..."]}
```

Run: `pytest tests/test_reports.py -v` Expected: PASS

- [ ] **Step 6.4: Commit** `feat(backend): deep analysis + daily/weekly/monthly report builders`

### Task 7: FastAPI 路由 + RSS 输出

**Files:**
- Create: `backend/app/api/__init__.py`, `backend/app/api/main.py`, `backend/tests/test_api.py`

- [ ] **Step 7.1: 失败测试**（TestClient：GET /api/reports 列表与 ?type=daily&date= 过滤；GET /api/items?category=&q= LIKE 搜索；POST /api/subscriptions 创建+confirm token 流转；GET /rss/daily.xml 是合法 XML 且含 item；admin 无 token 401，带 token 可触发 POST /api/admin/run/ingest）

- [ ] **Step 7.2: 实现 main.py**

路由清单（全部 JSON，除 /rss/*）：

```
GET  /api/reports?type=&limit=20            → [{id,type,period_date,title,created_at}]
GET  /api/reports/{type}/{period_date}      → 全文（markdown/html/headline_analysis/stats）
GET  /api/items?category=&source=&q=&min_score=&limit=50&offset=0
      # q: title/summary LIKE（Postgres 后续换 FTS，接口不变）
POST /api/subscriptions {email, frequencies[]}      → 201 + 发确认邮件（SMTP 未配则记日志跳过）
GET  /api/subscriptions/confirm?token=              → confirmed=True
GET  /api/subscriptions/unsubscribe?token=          → 删除
GET  /rss/{daily|weekly|monthly}.xml                → 最近 20 份该类报告
GET  /rss/feed.xml                                  → 最近 100 条 enriched 条目
POST /api/admin/run/{ingest|enrich|daily|weekly}    → Bearer admin_token，手动触发
GET  /api/admin/status                              → 源状态 + 最近 PipelineRun + token 成本合计
CORS: allow http://localhost:3000 与 settings.site_base_url
```

Run: `pytest tests/test_api.py -v` Expected: PASS

- [ ] **Step 7.3: Commit** `feat(backend): REST API + RSS endpoints`

### Task 8: 分发（邮件/webhook）+ 调度器

**Files:**
- Create: `backend/app/delivery/__init__.py`, `email.py`, `webhook.py`, `backend/app/scheduler.py`（测试并入 test_api.py 的 delivery 节）

- [ ] **Step 8.1: 失败测试**（smtplib/httpx mock：deliver_report 对每个 confirmed 订阅者发信并写 DeliveryLog；SMTP 未配置 → DeliveryLog status="skipped"；webhook 未配置同理；失败重试 2 次后 status="failed"）

- [ ] **Step 8.2: 实现**

```python
# email.py: send_html(to, subject, html)（smtplib.SMTP_SSL/starttls 按端口）；
#   deliver_report(session, report)：遍历订阅 frequencies 匹配 report.type
# webhook.py: push_wecom(text_md)（POST {"msgtype":"markdown",...}）；
#   push_telegram(text)；push_report_card(report)：头条标题×3 + 链接
# scheduler.py: BackgroundScheduler(timezone=Asia/Shanghai)
#   every 2h → run_ingest+run_enrich；cron 07:00 → build_daily+deliver
#   mon 07:30 → build_weekly+deliver；day1 08:00 → build_monthly+deliver
#   起停挂 FastAPI lifespan，INTEL_SCHEDULER_ENABLED=0 可关（测试/CI 关）
```

Run: `pytest tests/ -v` Expected: 全套 PASS

- [ ] **Step 8.3: Commit** `feat(backend): delivery channels + scheduler`

### Task 9: Next.js 前端

**Files:**
- Create: `frontend/` 全套（见文件地图）

- [ ] **Step 9.1: 脚手架**

Run: `cd frontend && npx -y create-next-app@latest . --ts --tailwind --app --no-src-dir --import-alias "@/*" --use-npm --yes`
Expected: 创建成功（npx 不可交互参数以实际版本为准，失败则手写 package.json 等价骨架）

- [ ] **Step 9.2: lib/api.ts**

```typescript
const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
export async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { next: { revalidate: 60 } });
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}
export interface ReportMeta { id:number; type:string; period_date:string; title:string; created_at:string }
export interface ReportFull extends ReportMeta { markdown:string; html:string; headline_analysis:string; stats:string }
export interface FeedItem { id:number; title:string; url:string; source:string; published_at:string|null;
  summary_zh:string; category:string; tags:string[]; importance_score:number }
```

- [ ] **Step 9.3: 页面实现**（Server Components 直取 API；样式 Tailwind 简洁阅读版式：max-w-3xl 居中、prose 渲染报告 HTML）

- layout.tsx：顶导航（AI 情报站 / 报告归档 / 信息流 / 搜索 / 订阅），深色友好
- page.tsx：`getJSON('/api/reports?type=daily&limit=1')` → 取详情渲染 html（`dangerouslySetInnerHTML`）+ 右侧近 7 份报告列表
- reports/page.tsx：三个 tab(daily/weekly/monthly) 列表 → 链接到详情
- reports/[type]/[date]/page.tsx：详情渲染
- feed/page.tsx：searchParams 过滤（category/source/min_score），重要度徽章（≥8 红 / ≥6 橙 / 其他灰），每条卡片：标题(外链)+摘要+标签+来源+时间
- search/page.tsx：?q= 透传 /api/items
- subscribe/page.tsx：client component 表单（email + 三个 checkbox）POST，成功/失败提示

- [ ] **Step 9.4: 构建验证**

Run: `cd frontend && npm run build`
Expected: build 成功，全部路由编译通过

- [ ] **Step 9.5: Commit** `feat(frontend): Next.js site (home/reports/feed/search/subscribe)`

### Task 10: 部署交付物 + README

**Files:**
- Create: `deploy/docker-compose.yml`, `deploy/Dockerfile.api`, `deploy/Dockerfile.web`, `deploy/Caddyfile`, `deploy/.env.example`, `README.md`

- [ ] **Step 10.1: docker-compose.yml**（五服务：db=postgres:16-alpine + healthcheck；api build Dockerfile.api，INTEL_DB_URL=postgresql+psycopg://…，depends_on db healthy；web build Dockerfile.web；rsshub=diygod/rsshub 镜像；caddy 反代 80/443，volume caddy_data；api 环境 LLM_PROVIDER=anthropic-api）
- [ ] **Step 10.2: Caddyfile**（`:80` → `/api/* /rss/*` 反代 api:8000，其余反代 web:3000；域名占位注释）
- [ ] **Step 10.3: README.md**（本地运行三命令 / VPS 部署步骤 / 环境变量表 / 源管理与成本说明）
- [ ] **Step 10.4: Commit** `feat(deploy): docker compose + caddy + README`

### Task 11: 真实运行 — 生成 6.12 日报与本周周报

**Files:**
- Modify: `data/`（运行产物）；必要时修正 seeds URL/解析

- [ ] **Step 11.1: 初始化** `cd backend && .venv/bin/python -c "from app.db import init_db; init_db()"` + seed_sources
- [ ] **Step 11.2: 起 API** `uvicorn app.api.main:app --port 8000`（后台）
- [ ] **Step 11.3: 真实抓取** `curl -X POST -H "Authorization: Bearer $TOKEN" localhost:8000/api/admin/run/ingest` → 看 /api/admin/status：≥15 源 ok、新条目 ≥80；对 404 源现场修 URL 或置 degraded
- [ ] **Step 11.4: 真实 enrich**（claude-cli provider）→ 抽查 10 条摘要质量（中文、分类合理）
- [ ] **Step 11.5: 生成日报** POST /api/admin/run/daily → 检查 data/reports/daily-2026-06-12.md：头条≥3 条且五段齐全、四分类有内容、管道状态如实
- [ ] **Step 11.6: 生成周报** POST /api/admin/run/weekly → weekly-2026-W24.md 趋势四维齐全
- [ ] **Step 11.7: 前端验证** `npm run dev` → 首页渲染日报、归档/详情/feed/搜索/订阅页全可用（浏览器实测截图）
- [ ] **Step 11.8: Commit** `feat: first real daily/weekly reports generated`

### Task 12: 收尾

- [ ] 全套测试最终跑：`pytest tests/ -v` 全绿
- [ ] git log 整理确认 + 最终 commit
- [ ] 调用 conversation-logging skill 沉淀里程碑（系统建成 + 双报告产出）

---

## Self-Review 记录

- **Spec 覆盖**：架构五容器→Task10；25源→Task4 seeds（26含2个X源）；四级管道→Task4/5/6；日周月报→Task6（月报 build_monthly 与 weekly 同构，period=当月）；网站六页→Task9（admin 页面以 API+curl 代替 UI，spec §8 admin 功能由 /api/admin/* 提供——前端 admin UI 列为后续增量，不阻塞核心价值）；订阅确认/退订→Task7/8；RSS 4 路→Task7；调度→Task8；错误处理（源降级/LLM重试/分发重试）→Task4/2/8；测试策略→各任务 TDD+mock。
- **占位符扫描**：无 TBD；Task9 页面与 Task10 部署文件以规格说明给出（交付时写完整代码）。
- **类型一致性**：Report.period_date 统一字符串（daily 用日期/weekly 用 2026-W24/monthly 用 2026-06）；category 枚举 paradigm|tech|opensource|product 全文一致；RawItem 字段在 fetchers/ingest 间一致。
- **偏差声明**：admin 前端页面降级为 REST API（个人自用 curl/后续补 UI），其余与 spec 一致。
