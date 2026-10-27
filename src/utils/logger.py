"""
src/utils/logger.py — Structured JSON logger factory.

All pipeline logs are emitted as JSON so they are machine-parseable
by log aggregators (CloudWatch, Datadog, Splunk, etc.).

Usage:
    from src.utils.logger import get_logger
    log = get_logger("stripe")
    log.info("pages_downloaded", pages=3, rows=250)

Output:
    {"timestamp": "...", "level": "INFO", "logger": "stripe",
     "message": "pages_downloaded | pages=3 rows=250", ...}
"""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """
    Render every log record as a single-line JSON object.

    Fixed fields: timestamp, level, logger, message, module, line.
    Any structured context from EtlLogger is included in the message.
    """

    _RESERVED_ATTRS = frozenset(
        logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
        | {"message", "asctime"}
    )

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "message": record.message,
        }
        for key, val in record.__dict__.items():
            if key not in self._RESERVED_ATTRS:
                payload[key] = val
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class EtlLogger:
    """
    Structured logger wrapper.

    Allows structured key=value arguments:
        log.info("event", rows=5, source="stripe")
    These are formatted into the message string, compatible with
    all Python versions including 3.9.
    """

    def __init__(self, name: str):
        self._log = logging.getLogger(f"etl.{name}")
        # Don't add handlers twice
        if not self._log.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JsonFormatter())
            self._log.addHandler(handler)
            self._log.propagate = False
        self._log.setLevel(logging.INFO)

    def _format(self, event: str, extra: dict) -> str:
        """Format event and key=value pairs into a single message string."""
        details = " ".join(f"{k}={v}" for k, v in extra.items())
        return f"{event} | {details}" if details else event

    def info(self, event: str, **extra) -> None:
        self._log.info(self._format(event, extra))

    def warning(self, event: str, **extra) -> None:
        self._log.warning(self._format(event, extra))

    def error(self, event: str, **extra) -> None:
        self._log.error(self._format(event, extra))


def get_logger(name: str = "etl", level: Optional[str] = None) -> EtlLogger:
    """
    Return an EtlLogger for the given name.

    Args:
        name:  Short name for this logger, e.g. "stripe", "pipeline".
        level: Override log level (e.g. "DEBUG"). Defaults to "INFO".

    Returns:
        An EtlLogger instance that supports log.info("event", key=value).
    """
    return EtlLogger(name)
