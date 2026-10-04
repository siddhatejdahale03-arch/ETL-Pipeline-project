"""Send Slack / Email messages when the pipeline fails (or finishes)."""
import smtplib
from email.mime.text import MIMEText

import requests

from config.settings import get_settings
from src.utils.logger import get_logger

log = get_logger("alerts")


def send_slack_alert(message: str) -> None:
    """Post a message to Slack using an Incoming Webhook URL."""
    settings = get_settings()
    if not settings.slack_webhook_url:  # Slack is optional — not set up, so do nothing
        return
    try:
        requests.post(settings.slack_webhook_url, json={"text": message}, timeout=10)
        log.info("slack_alert_sent")
    except requests.RequestException as error:
        log.error("slack_alert_failed", error=error)


def send_email_alert(subject: str, body: str) -> None:
    """Send a plain-text email to ALERT_EMAIL."""
    settings = get_settings()
    if not settings.alert_email:
        log.warning("email_skipped", reason="ALERT_EMAIL is empty")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user or "etl-bot@example.com"
    msg["To"] = settings.alert_email
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()  # encrypt the connection (Gmail requires this)
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        log.info("email_alert_sent", to=settings.alert_email)
    except (OSError, smtplib.SMTPException) as error:
        log.error("email_alert_failed", error=error)


def alert_on_failure(context: dict) -> None:
    """
    Airflow calls this function automatically when a task fails.
    `context` is a dictionary Airflow gives us with details about the run.
    """
    task = context.get("task_instance")
    dag_id = task.dag_id if task else "unknown"
    task_id = task.task_id if task else "unknown"
    error = context.get("exception", "unknown error")

    message = f"ETL FAILED | DAG: {dag_id} | Task: {task_id} | Error: {error}"
    send_slack_alert(message)
    send_email_alert("ETL pipeline failed", message)
