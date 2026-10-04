"""Retry decorator using Tenacity with exponential backoff."""
import logging
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


def api_retry(max_attempts: int = 5):
    """Decorator: retries on network errors with exponential backoff."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type(
            (requests.exceptions.RequestException, ConnectionError, TimeoutError)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )