"""Code shared by every extractor: one safe GET request + demo data loading."""
import json
import time

import requests

from config.settings import PROJECT_ROOT
from src.utils.logger import get_logger
from src.utils.retry import RateLimitError, api_retry

log = get_logger("extractor")

SAMPLE_FOLDER = PROJECT_ROOT / "data" / "sample"


@api_retry
def get_json(url: str, headers: dict, params: dict | None = None) -> dict:
    """
    Call an API with GET and return the JSON body.

    - 429 (rate limit): wait the time the API asks for, then retry.
    - Other 4xx/5xx errors: raise an error.
    """
    response = requests.get(url, headers=headers, params=params, timeout=30)

    if response.status_code == 429:
        wait_seconds = int(response.headers.get("Retry-After", 5))
        log.warning("rate_limited", url=url, wait_seconds=wait_seconds)
        time.sleep(wait_seconds)
        raise RateLimitError(url)  # @api_retry catches this and tries again

    response.raise_for_status()
    return response.json()


def load_sample(file_name: str) -> list[dict]:
    """Read a JSON file from data/sample/ (used in DEMO_MODE)."""
    with open(SAMPLE_FOLDER / file_name, encoding="utf-8") as f:
        return json.load(f)
