"""
extractors/stripe_extractor.py — Stripe Customer extractor.

Implements full cursor-based pagination to retrieve ALL customers from the
Stripe /v1/customers endpoint, not just the first page (100 records).

Key features:
  - Full pagination via `has_more` + `starting_after` cursor
  - Automatic retry on transient failures (429 rate limits, 5xx errors)
  - Request timeout to prevent hanging connections
  - Returns a validated List[Customer] (not raw dicts)
  - Structured logging at every page boundary

Stripe pagination docs:
    https://docs.stripe.com/api/pagination
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

import config
from extractors.base import BaseExtractor
from models.customer import Customer
from utils.logger import get_logger
from utils.retry import with_retry

logger = get_logger(__name__)

# Timeout (connect, read) in seconds for every Stripe API request
_REQUEST_TIMEOUT = (10, 30)


class StripeExtractor(BaseExtractor[Customer]):
    """
    Extracts all customers from the Stripe API.

    Usage:
        extractor = StripeExtractor()
        customers = extractor.extract()          # List[Customer]
        customers, elapsed = extractor.extract_with_timing()
    """

    source_name = "stripe"

    def __init__(
        self,
        api_key: Optional[str] = None,
        page_limit: int = 100,
    ) -> None:
        """
        Args:
            api_key:    Stripe secret key. Defaults to config.STRIPE_API_KEY.
            page_limit: Records per API page (1–100). Defaults to config.STRIPE_PAGE_LIMIT.
        """
        super().__init__()
        self._api_key = api_key or config.STRIPE_API_KEY
        self._page_limit = min(max(1, page_limit), 100)  # clamp to [1, 100]
        self._base_url = "https://api.stripe.com/v1"
        self._session = self._build_session()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_session(self) -> requests.Session:
        """Build a requests Session with auth headers pre-set."""
        session = requests.Session()
        session.headers.update(
            {
                "Authorization": f"Bearer {self._api_key}",
                "Stripe-Version": "2024-06-20",  # Pin to a stable API version
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        return session

    @with_retry(max_attempts=3, wait_min=1.0, wait_max=60.0, jitter=2.0)
    def _fetch_page(
        self,
        starting_after: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch a single page of customers from the Stripe API.

        Args:
            starting_after: Cursor for pagination (last customer ID from
                            previous page). None for the first page.

        Returns:
            Raw Stripe API response dict:
            {
                "object": "list",
                "data": [...],
                "has_more": bool,
                "url": "/v1/customers"
            }

        Raises:
            requests.HTTPError: On 4xx/5xx responses (after retries exhausted).
            requests.Timeout:   On connection/read timeout.
        """
        params: Dict[str, Any] = {"limit": self._page_limit}
        if starting_after:
            params["starting_after"] = starting_after

        logger.debug(
            "Fetching Stripe customers page",
            extra={"starting_after": starting_after, "limit": self._page_limit},
        )

        response = self._session.get(
            f"{self._base_url}/customers",
            params=params,
            timeout=_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def extract(self) -> List[Customer]:
        """
        Retrieve ALL customers from Stripe using cursor-based pagination.

        Iterates through pages until `has_more` is False, collecting every
        customer into a single list.  Each raw dict is validated against the
        Customer Pydantic model (invalid records are logged and skipped).

        Returns:
            Flat list of validated Customer objects.
        """
        all_customers: List[Customer] = []
        starting_after: Optional[str] = None
        page_number = 0

        logger.info(
            "Starting Stripe customer extraction",
            extra={"source": self.source_name, "page_limit": self._page_limit},
        )

        while True:
            page_number += 1
            page_data = self._fetch_page(starting_after=starting_after)

            raw_records: List[Dict[str, Any]] = page_data.get("data", [])
            has_more: bool = page_data.get("has_more", False)

            # Validate and convert each record
            page_customers: List[Customer] = []
            for raw in raw_records:
                try:
                    page_customers.append(Customer.model_validate(raw))
                except Exception as exc:
                    logger.warning(
                        "Failed to validate customer record — skipping",
                        extra={
                            "customer_id": raw.get("id", "unknown"),
                            "error": str(exc),
                        },
                    )

            all_customers.extend(page_customers)

            logger.info(
                "Fetched page",
                extra={
                    "page": page_number,
                    "page_count": len(page_customers),
                    "total_so_far": len(all_customers),
                    "has_more": has_more,
                },
            )

            if not has_more or not raw_records:
                break

            # Advance cursor to the last record's ID
            starting_after = raw_records[-1]["id"]

        logger.info(
            "Stripe extraction finished",
            extra={
                "total_customers": len(all_customers),
                "total_pages": page_number,
            },
        )

        return all_customers
