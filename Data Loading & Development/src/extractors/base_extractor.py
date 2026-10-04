"""Abstract base class for API extractors."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generator

import requests
from src.utils.logger import get_logger
from src.utils.retry import api_retry

log = get_logger("base_extractor")


class BaseExtractor(ABC):
    """Base class providing retry + pagination primitives."""

    name: str = "base"

    def __init__(self, base_url: str, headers: Dict[str, str]):
        self.base_url = base_url.rstrip("/")
        self.headers = headers
        self.session = requests.Session()
        self.session.headers.update(headers)

    @api_retry(max_attempts=5)
    def _get(self, url: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        log.info("http_get", url=url, params=params)
        resp = self.session.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", "5"))
            log.warning("rate_limited", retry_after=retry_after)
            raise requests.exceptions.RequestException("Rate limited")
        resp.raise_for_status()
        return resp.json()

    @abstractmethod
    def extract(
        self, since: str | None = None
    ) -> Generator[Dict[str, Any], None, None]:
        raise NotImplementedError