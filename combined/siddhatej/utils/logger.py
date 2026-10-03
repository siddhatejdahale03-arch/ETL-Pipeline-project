"""
utils/logger.py — Structured JSON logger factory.

All pipeline logs are emitted as JSON so they are machine-parseable
by log aggregators (CloudWatch, Datadog, Splunk, etc.).

Usage:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Fetched customers", extra={"count": 42, "source": "stripe"})
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """
    Render every log record as a single-line JSON object.

    Fixed fields:
        timestamp  — ISO 8601 UTC
        level      — DEBUG / INFO / WARNING / ERROR / CRITICAL
        logger     — logger name (usually __name__ of the calling module)
        message    — the log message
        module     — source file module
        line       — line number in source file

    Any keyword arguments passed via `extra={}` are merged into the top-level
    JSON object, making it easy to attach structured context.
    """

    # Keys that are always present on a LogRecord — we don't want to
    # duplicate them into the "extra" section.
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

        # Attach any extra structured fields the caller passed in
        for key, val in record.__dict__.items():
            if key not in self._RESERVED_ATTRS:
                payload[key] = val

        # Attach exception info if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Return a named logger configured with the JSON formatter.

    Args:
        name:  Usually ``__name__`` of the calling module.
        level: Override log level (e.g. "DEBUG"). Falls back to the
               value in config (LOG_LEVEL env var → "INFO").

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    # Avoid circular imports: import config lazily
    if level is None:
        try:
            from config import LOG_LEVEL
            level = LOG_LEVEL
        except Exception:
            level = "INFO"

    logger = logging.getLogger(name)

    # Don't add handlers twice if this function is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
