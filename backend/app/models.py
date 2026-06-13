from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    category: Mapped[str]  # vendor | paradigm | community | media | twitter
    url: Mapped[str]
    fetch_method: Mapped[str]  # rss | hackernews | github_trending | hf_papers | hf_models | reddit | rsshub
    enabled: Mapped[bool] = mapped_column(default=True)
    fail_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="ok")  # ok | degraded
    last_fetched_at: Mapped[datetime | None] = mapped_column(default=None)


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    title: Mapped[str]
    url: Mapped[str]
    author: Mapped[str] = mapped_column(default="")
    published_at: Mapped[datetime | None] = mapped_column(default=None)
    raw_content: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str] = mapped_column(unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Enrichment(Base):
    __tablename__ = "enrichments"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), unique=True)
    summary_zh: Mapped[str] = mapped_column(Text)
    category: Mapped[str]  # 8 类：model-release|dev-tooling|agent-infra|research|opensource|product-launch|business|policy-safety
    tags: Mapped[str] = mapped_column(default="[]")  # JSON list 主题标签
    entities: Mapped[str] = mapped_column(default="[]")  # JSON list 公司/产品/模型规范名
    importance_score: Mapped[int] = mapped_column(default=5)
    model: Mapped[str] = mapped_column(default="")
    tokens_in: Mapped[int] = mapped_column(default=0)
    tokens_out: Mapped[int] = mapped_column(default=0)
    cost_usd: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("type", "period_date", "lens"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]  # daily | weekly | monthly
    period_date: Mapped[str]  # daily: 2026-06-12 / weekly: 2026-W24 / monthly: 2026-06
    lens: Mapped[str] = mapped_column(default="pm")  # 视角：pm | engineer | investor | researcher
    title: Mapped[str]
    markdown: Mapped[str] = mapped_column(Text)
    html: Mapped[str] = mapped_column(Text)
    headline_analysis: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    stats: Mapped[str] = mapped_column(Text, default="{}")  # JSON
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    frequencies: Mapped[str] = mapped_column(default='["daily"]')  # JSON list
    confirmed: Mapped[bool] = mapped_column(default=False)
    confirm_token: Mapped[str] = mapped_column(default="")
    unsubscribe_token: Mapped[str] = mapped_column(default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"))
    channel: Mapped[str]  # email | wecom | telegram
    target: Mapped[str] = mapped_column(default="")
    status: Mapped[str] = mapped_column(default="pending")  # pending | sent | skipped | failed
    retries: Mapped[int] = mapped_column(default=0)
    error: Mapped[str] = mapped_column(default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    stage: Mapped[str]  # ingest | enrich | report_daily | report_weekly | report_monthly | deliver
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="running")  # running | success | failed
    detail: Mapped[str] = mapped_column(Text, default="{}")  # JSON
