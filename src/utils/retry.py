"""
Retry helper built on the Tenacity library.

If an API call fails because of a network problem or a "too many requests"
error, we wait a little and try again (2s, 4s, 8s ...).

Usage:
    @api_retry
    def fetch_data(url):
        return requests.get(url).json()
"""
import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config.settings import get_settings


class RateLimitError(Exception):
    """Raised when an API answers 429 Too Many Requests."""


# Errors that are worth retrying
RETRYABLE_ERRORS = (
    RateLimitError,
    requests.ConnectionError,
    requests.Timeout,
)

# Decorator: put @api_retry above any function that calls an API
# Waits 2s, 4s, 8s... between retries (exponential back-off)
api_retry = retry(
    retry=retry_if_exception_type(RETRYABLE_ERRORS),
    stop=stop_after_attempt(get_settings().max_retry_attempts),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,  # re-raise the last exception if all retries are exhausted
)
