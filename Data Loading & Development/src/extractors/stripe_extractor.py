"""Stripe extractor with cursor-based pagination."""
from typing import Any, Dict, Generator

from config.settings import get_settings
from src.extractors.base_extractor import BaseExtractor
from src.utils.logger import get_logger

settings = get_settings()
log = get_logger("stripe_extractor")


class StripeExtractor(BaseExtractor):
    name = "stripe"

    def __init__(self):
        super().__init__(
            base_url=settings.stripe_base_url,
            headers={"Authorization": f"Bearer {settings.stripe_api_key}"},
        )

    def _paginate(self, endpoint: str, params: Dict[str, Any] | None = None):
        params = dict(params or {})
        params.setdefault("limit", 100)
        starting_after = None

        while True:
            if starting_after:
                params["starting_after"] = starting_after
            payload = self._get(f"{self.base_url}/{endpoint}", params=params)
            data = payload.get("data", [])
            if not data:
                break
            for record in data:
                yield record
            if not payload.get("has_more"):
                break
            starting_after = data[-1]["id"]

    def extract(
        self, since: str | None = None
    ) -> Generator[Dict[str, Any], None, None]:
        log.info("stripe_extract_start", since=since)
        for customer in self._paginate("customers"):
            yield {"_type": "customer", **customer}

        params = {"created[gte]": since} if since else None
        for charge in self._paginate("charges", params=params):
            yield {"_type": "charge", **charge}