"""SMTP 邮件分发：报告推送 + 订阅确认邮件。未配置 SMTP 时记 skipped 不报错。"""

import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import DeliveryLog, Report, Subscription, utcnow

MAX_RETRIES = 2


def smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.mail_from)


def send_html(to: str, subject: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.mail_from
    msg["To"] = to
    msg.attach(MIMEText(html, "html", "utf-8"))
    if settings.smtp_port == 465:
        server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30)
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)
        server.starttls()
    try:
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
    finally:
        server.quit()


def _wrap_email_html(report: Report) -> str:
    footer = (
        f'<hr><p style="color:#888;font-size:12px">AI 情报站 · '
        f'<a href="{settings.site_base_url}/reports/{report.type}/{report.period_date}">网页版</a> · '
        f"邮件底部退订链接因人而异，见每封邮件尾部</p>"
    )
    return f'<div style="max-width:720px;margin:0 auto;font-family:system-ui,sans-serif">{report.html}{footer}</div>'


def deliver_report_email(session: Session, report: Report) -> dict:
    subs = (
        session.execute(select(Subscription).where(Subscription.confirmed.is_(True)))
        .scalars()
        .all()
    )
    targets = [s for s in subs if report.type in json.loads(s.frequencies or "[]")]
    sent = skipped = failed = 0
    for sub in targets:
        log = DeliveryLog(report_id=report.id, channel="email", target=sub.email)
        session.add(log)
        if not smtp_configured():
            log.status = "skipped"
            log.error = "SMTP not configured"
            skipped += 1
            continue
        html = _wrap_email_html(report) + (
            f'<p style="font-size:12px;color:#aaa"><a href="{settings.site_base_url.rstrip("/")}'
            f'/api/subscriptions/unsubscribe?token={sub.unsubscribe_token}">退订</a></p>'
        )
        for attempt in range(MAX_RETRIES + 1):
            try:
                send_html(sub.email, report.title, html)
                log.status = "sent"
                sent += 1
                break
            except Exception as e:
                log.retries = attempt
                log.error = f"{type(e).__name__}: {str(e)[:200]}"
                if attempt == MAX_RETRIES:
                    log.status = "failed"
                    failed += 1
    session.commit()
    return {"sent": sent, "skipped": skipped, "failed": failed, "targets": len(targets)}


def send_confirm_email(session: Session, sub: Subscription) -> bool:
    """发订阅确认邮件；SMTP 未配置返回 False（订阅仍保留，待人工确认或后台确认）。"""
    if not smtp_configured():
        return False
    confirm_url = f"{settings.site_base_url.rstrip('/')}/api/subscriptions/confirm?token={sub.confirm_token}"
    html = (
        f"<p>您正在订阅 AI 情报站报告，点击确认：</p>"
        f'<p><a href="{confirm_url}">{confirm_url}</a></p>'
    )
    try:
        send_html(sub.email, "确认订阅 AI 情报站", html)
        return True
    except Exception:
        return False
