"""
utils/retry.py — Reusable tenacity retry decorators for external API calls.

Provides a pre-configured decorator (`with_retry`) that handles:
  - Transient HTTP errors (429 Too Many Requests, 5xx Server Errors)
  - Network-level exceptions (ConnectionError, Timeout)
  - Exponential backoff with jitter to avoid thundering herd

Usage:
    from utils.retry import with_retry

    @with_retry()
    def call_some_api():
        ...

    # Or with custom settings:
    @with_retry(max_attempts=5, wait_min=2, wait_max=30)
    def call_flaky_api():
        ...
"""

import requests
from functools import wraps
from typing import Any, Callable, Tuple, Type

from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
    before_sleep_log,
    RetryCallState,
)
import logging

# Use a dedicated logger for retry events
_retry_logger = logging.getLogger("etl.retry")


def _is_retryable(exc: BaseException) -> bool:
    """
    Return True if the exception should trigger a retry.

    Retryable conditions:
      - requests.Timeout
      - requests.ConnectionError
      - requests.HTTPError with status 429 (rate limit) or 5xx (server error)
    """
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True
    if isinstance(exc, requests.HTTPError):
        status = exc.response.status_code if exc.response is not None else None
        return status == 429 or (status is not None and status >= 500)
    return False


def with_retry(
    max_attempts: int = 3,
    wait_min: float = 1.0,
    wait_max: float = 60.0,
    jitter: float = 2.0,
) -> Callable:
    """
    Decorator factory that wraps a function with retry logic.

    Args:
        max_attempts: Total number of attempts (first call + retries).
        wait_min:     Minimum wait time in seconds between retries.
        wait_max:     Maximum wait time in seconds between retries.
        jitter:       Random jitter added to each wait (seconds).

    Returns:
        A decorator that applies tenacity retry logic to the wrapped function.
    """

    def decorator(func: Callable) -> Callable:
        retrying_func = retry(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential_jitter(
                initial=wait_min,
                max=wait_max,
                jitter=jitter,
            ),
            before_sleep=before_sleep_log(_retry_logger, logging.WARNING),
            reraise=True,
        )(func)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return retrying_func(*args, **kwargs)

        return wrapper

    return decorator
