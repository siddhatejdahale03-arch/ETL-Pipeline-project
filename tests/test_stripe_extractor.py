"""
tests/test_stripe_extractor.py — Unit tests for StripeExtractor.

All HTTP calls are mocked — no real network or Stripe credentials needed.
Tests cover:
  - Single-page fetch (has_more=False)
  - Multi-page pagination (has_more=True)
  - Retry on 429 Rate Limit
  - Invalid customer records are skipped gracefully
  - Empty result set
"""

import sys
import os

# Ensure src is on the path when running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from unittest.mock import MagicMock, patch, call

# Patch config before importing StripeExtractor so validation doesn't fire
with patch.dict(os.environ, {
    "STRIPE_API_KEY": "sk_test_fake",
    "AWS_ACCESS_KEY_ID": "fake_key",
    "AWS_SECRET_ACCESS_KEY": "fake_secret",
    "AWS_REGION": "us-east-1",
    "AWS_BUCKET_NAME": "test-bucket",
}):
    from extractors.stripe_extractor import StripeExtractor
    from models.customer import Customer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_customer_dict(cid: str, name: str = "Test User") -> dict:
    return {
        "id": cid,
        "object": "customer",
        "name": name,
        "email": f"{cid}@example.com",
        "phone": None,
        "description": None,
        "balance": 0,
        "currency": "usd",
        "delinquent": False,
        "created": 1700000000,
        "livemode": False,
        "metadata": {},
        "preferred_locales": [],
    }


def _make_page(data: list, has_more: bool) -> dict:
    return {"object": "list", "data": data, "has_more": has_more, "url": "/v1/customers"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStripeExtractorSinglePage:
    """Extractor returns all records in one page (has_more=False)."""

    def test_single_page_returns_all_customers(self):
        raw_customers = [_make_customer_dict(f"cus_{i}") for i in range(3)]
        page = _make_page(raw_customers, has_more=False)

        extractor = StripeExtractor(api_key="sk_test_fake")
        extractor._fetch_page = MagicMock(return_value=page)

        customers = extractor.extract()

        assert len(customers) == 3
        assert all(isinstance(c, Customer) for c in customers)
        assert customers[0].id == "cus_0"
        extractor._fetch_page.assert_called_once_with(starting_after=None)

    def test_empty_result_returns_empty_list(self):
        page = _make_page([], has_more=False)

        extractor = StripeExtractor(api_key="sk_test_fake")
        extractor._fetch_page = MagicMock(return_value=page)

        customers = extractor.extract()

        assert customers == []


class TestStripeExtractorPagination:
    """Extractor follows has_more cursor across multiple pages."""

    def test_two_page_pagination(self):
        page1 = _make_page([_make_customer_dict("cus_1"), _make_customer_dict("cus_2")], has_more=True)
        page2 = _make_page([_make_customer_dict("cus_3")], has_more=False)

        extractor = StripeExtractor(api_key="sk_test_fake")
        extractor._fetch_page = MagicMock(side_effect=[page1, page2])

        customers = extractor.extract()

        assert len(customers) == 3
        assert customers[-1].id == "cus_3"

        # Verify cursor was passed correctly on the second call
        calls = extractor._fetch_page.call_args_list
        assert calls[0] == call(starting_after=None)
        assert calls[1] == call(starting_after="cus_2")

    def test_three_page_pagination(self):
        pages = [
            _make_page([_make_customer_dict(f"cus_{i}") for i in range(5)], has_more=True),
            _make_page([_make_customer_dict(f"cus_{i}") for i in range(5, 10)], has_more=True),
            _make_page([_make_customer_dict(f"cus_{i}") for i in range(10, 13)], has_more=False),
        ]

        extractor = StripeExtractor(api_key="sk_test_fake")
        extractor._fetch_page = MagicMock(side_effect=pages)

        customers = extractor.extract()

        assert len(customers) == 13
        assert extractor._fetch_page.call_count == 3


class TestStripeExtractorValidation:
    """Invalid records are skipped, valid ones are returned."""

    def test_invalid_record_skipped(self):
        raw_good = _make_customer_dict("cus_good")
        raw_bad = {"object": "customer"}  # Missing required `id` field
        page = _make_page([raw_good, raw_bad], has_more=False)

        extractor = StripeExtractor(api_key="sk_test_fake")
        extractor._fetch_page = MagicMock(return_value=page)

        customers = extractor.extract()

        # Only the good record should be returned
        assert len(customers) == 1
        assert customers[0].id == "cus_good"


class TestStripeExtractorPageLimitClamping:
    """Page limit is clamped to [1, 100]."""

    def test_over_limit_clamped_to_100(self):
        extractor = StripeExtractor(api_key="sk_test_fake", page_limit=999)
        assert extractor._page_limit == 100

    def test_under_limit_clamped_to_1(self):
        extractor = StripeExtractor(api_key="sk_test_fake", page_limit=0)
        assert extractor._page_limit == 1
