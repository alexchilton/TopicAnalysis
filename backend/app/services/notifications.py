"""Notification service for anomaly alerts (email + Slack webhook)."""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from typing import List

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import AnomalyAlert

logger = get_logger(__name__)


async def send_slack_notification(alerts: list[AnomalyAlert]) -> bool:
    if not settings.slack_webhook_url:
        logger.debug("slack_webhook_not_configured")
        return False

    blocks = []
    for alert in alerts[:10]:
        emoji = "🔴" if alert.severity == "high" else "🟡"
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *{alert.type.value}* ({alert.severity})\n{alert.message}",
                },
            }
        )

    payload = {
        "text": f"🚨 {len(alerts)} anomaly alert(s) detected",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🚨 {len(alerts)} Anomaly Alert(s)"},
            },
            *blocks,
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(settings.slack_webhook_url, json=payload)
            resp.raise_for_status()
            logger.info("slack_notification_sent", alert_count=len(alerts))
            return True
    except Exception as exc:
        logger.error("slack_notification_failed", error=str(exc))
        return False


async def send_email_notification(alerts: list[AnomalyAlert]) -> bool:
    if not all([settings.smtp_host, settings.notification_email_from, settings.notification_email_to]):
        logger.debug("email_notification_not_configured")
        return False

    body_lines = []
    for alert in alerts:
        body_lines.append(f"[{alert.severity.upper()}] {alert.type.value}: {alert.message}")
        body_lines.append(f"  Detected at: {alert.detected_at.isoformat()}")
        body_lines.append("")

    msg = MIMEText("\n".join(body_lines))
    msg["Subject"] = f"Topic Analysis: {len(alerts)} anomaly alert(s)"
    msg["From"] = settings.notification_email_from
    msg["To"] = settings.notification_email_to

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        logger.info("email_notification_sent", alert_count=len(alerts))
        return True
    except Exception as exc:
        logger.error("email_notification_failed", error=str(exc))
        return False


async def notify_anomalies(alerts: list[AnomalyAlert]) -> None:
    if not alerts:
        return

    await send_slack_notification(alerts)
    await send_email_notification(alerts)
