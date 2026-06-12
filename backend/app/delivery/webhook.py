"""企业微信 / Telegram webhook 推送：报告生成后推「头条 + 链接」卡片。"""

import json

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import DeliveryLog, Report

MAX_RETRIES = 2


def _report_digest(report: Report) -> str:
    headlines = json.loads(report.headline_analysis or "[]")
    lines = [f"**{report.title}**"]
    for h in headlines[:3]:
        lines.append(f"- {h.get('headline', '')}")
    if not headlines:
        stats = json.loads(report.stats or "{}")
        lines.append(f"本期收录 {stats.get('total', 0)} 条")
    lines.append(f"全文：{settings.site_base_url.rstrip('/')}/reports/{report.type}/{report.period_date}")
    return "\n".join(lines)


def _push_with_retry(session: Session, report: Report, channel: str, target: str, do_push) -> str:
    log = DeliveryLog(report_id=report.id, channel=channel, target=target)
    session.add(log)
    if not target:
        log.status = "skipped"
        log.error = f"{channel} not configured"
        session.commit()
        return "skipped"
    for attempt in range(MAX_RETRIES + 1):
        try:
            do_push()
            log.status = "sent"
            break
        except Exception as e:
            log.retries = attempt
            log.error = f"{type(e).__name__}: {str(e)[:200]}"
            if attempt == MAX_RETRIES:
                log.status = "failed"
    session.commit()
    return log.status


def push_wecom(session: Session, report: Report) -> str:
    url = settings.wecom_webhook_url

    def do_push():
        r = httpx.post(url, json={"msgtype": "markdown", "markdown": {"content": _report_digest(report)}}, timeout=15)
        r.raise_for_status()

    return _push_with_retry(session, report, "wecom", url, do_push)


def push_telegram(session: Session, report: Report) -> str:
    token, chat_id = settings.telegram_bot_token, settings.telegram_chat_id
    target = f"chat:{chat_id}" if token and chat_id else ""

    def do_push():
        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": _report_digest(report).replace("**", ""), "disable_web_page_preview": True},
            timeout=15,
        )
        r.raise_for_status()

    return _push_with_retry(session, report, "telegram", target, do_push)


def deliver_report_webhooks(session: Session, report: Report) -> dict:
    return {"wecom": push_wecom(session, report), "telegram": push_telegram(session, report)}
