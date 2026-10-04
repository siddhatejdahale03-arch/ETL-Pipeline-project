"""
Simple logger.

Usage:
    log = get_logger("stripe")
    log.info("pages_downloaded", pages=3, rows=250)

Output:
    2026-10-04 10:00:00 | INFO | stripe | pages_downloaded | pages=3 rows=250

Logs go to the screen AND to logs/etl.log.
"""
import logging

from config.settings import PROJECT_ROOT, get_settings

LOG_FILE = PROJECT_ROOT / "logs" / "etl.log"


def _setup_root_logger() -> None:
    root = logging.getLogger("etl")
    if root.handlers:  # already set up
        return

    root.setLevel(get_settings().log_level.upper())
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")

    screen = logging.StreamHandler()
    screen.setFormatter(fmt)
    root.addHandler(screen)

    LOG_FILE.parent.mkdir(exist_ok=True)
    file = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file.setFormatter(fmt)
    root.addHandler(file)


class EtlLogger:
    """Small wrapper so we can write log.info("event", key=value)."""

    def __init__(self, name: str):
        self.name = name
        self._log = logging.getLogger(f"etl.{name}")

    def _format(self, event: str, extra: dict) -> str:
        details = " ".join(f"{key}={value}" for key, value in extra.items())
        return f"{self.name} | {event} | {details}"

    def info(self, event: str, **extra) -> None:
        self._log.info(self._format(event, extra))

    def warning(self, event: str, **extra) -> None:
        self._log.warning(self._format(event, extra))

    def error(self, event: str, **extra) -> None:
        self._log.error(self._format(event, extra))


def get_logger(name: str = "etl") -> EtlLogger:
    _setup_root_logger()
    return EtlLogger(name)
