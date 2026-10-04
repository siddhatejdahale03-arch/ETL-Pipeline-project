"""Slack & Email alerting helpers."""
import smtplib
from email.mime.text import MIMEText

import requests

from config.settings import get_settings
from src.utils.logger import get_logger

settings = get_settings()
log = get_logger("alerts")


def send_slack_alert(message: str, channel: str = "#data-alerts") -> None:
    if not settings.slack_webhook_url:
        log.warning("slack_webhook_missing")
        return
    try:
        requests.post(settings.slack_webhook_url, json={"text": message}, timeout=10)
        log.info("slack_alert_sent", channel=channel)
    except Exception as e:
        log.error("slack_alert_failed", error=str(e))


def send_email_alert(subject: str, body: str) -> None:
    if not settings.alert_email:
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "etl-bot@example.com"
    msg["To"] = settings.alert_email
    try:
        with smtplib.SMTP("localhost") as server:
            server.send_message(msg)
    except Exception as e:
        log.error("email_alert_failed", error=str(e))


def alert_on_failure(context: dict) -> None:
    """Airflow on_failure_callback."""
    dag_id = context.get("dag").dag_id if context.get("dag") else "unknown"
    task_id = (
        context.get("task_instance").task_id
        if context.get("task_instance")
        else "unknown"
    )
    send_slack_alert(f"❌ *ETL Failure* | DAG: `{dag_id}` | Task: `{task_id}`")