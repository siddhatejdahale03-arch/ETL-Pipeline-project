"""Unit tests for extractors (mocked HTTP, no real API calls)."""
from unittest.mock import patch, MagicMock

import pytest

from src.extractors.stripe_extractor import StripeExtractor
from src.extractors.salesforce_extractor import SalesforceExtractor


# =========================================================
# Stripe extractor
# =========================================================

def test_stripe_extractor_headers():
    """Ensure Authorization header is set from settings."""
    ex = StripeExtractor()
    assert "Authorization" in ex.session.headers
    assert ex.session.headers["Authorization"].startswith("Bearer ")


@patch("src.extractors.base_extractor.BaseExtractor._get")
def test_stripe_extractor_single_page(mock_get):
    """One page of customers, then one page of charges."""
    mock_get.side_effect = [
        # customers page
        {
            "data": [
                {"id": "cus_1", "email": "a@b.com", "created": 1700000000},
                {"id": "cus_2", "email": "c@d.com", "created": 1700000001},
            ],
            "has_more": False,
        },
        # charges page
        {
            "data": [
                {
                    "id": "ch_1",
                    "amount": 1000,
                    "currency": "usd",
                    "status": "succeeded",
                    "created": 1700000000,
                }
            ],
            "has_more": False,
        },
    ]

    ex = StripeExtractor()
    records = list(ex.extract(since=None))

    types = [r["_type"] for r in records]
    assert types.count("customer") == 2
    assert types.count("charge") == 1
    assert mock_get.call_count == 2


@patch("src.extractors.base_extractor.BaseExtractor._get")
def test_stripe_extractor_pagination(mock_get):
    """Two pages of customers using cursor-based pagination."""
    mock_get.side_effect = [
        {
            "data": [{"id": "cus_1", "created": 1}],
            "has_more": True,
        },
        {
            "data": [{"id": "cus_2", "created": 2}],
            "has_more": False,
        },
        # charges (empty)
        {"data": [], "has_more": False},
    ]

    ex = StripeExtractor()
    customers = [r for r in ex.extract() if r["_type"] == "customer"]
    assert len(customers) == 2
    assert customers[0]["id"] == "cus_1"
    assert customers[1]["id"] == "cus_2"


def test_stripe_extractor_is_base_extractor():
    from src.extractors.base_extractor import BaseExtractor

    assert issubclass(StripeExtractor, BaseExtractor)


# =========================================================
# Salesforce extractor
# =========================================================

def test_salesforce_extractor_is_base_extractor():
    from src.extractors.base_extractor import BaseExtractor

    assert issubclass(SalesforceExtractor, BaseExtractor)


@patch("src.extractors.salesforce_extractor.requests.post")
@patch("src.extractors.base_extractor.BaseExtractor._get")
def test_salesforce_extractor_extract(mock_get, mock_post):
    """Mock OAuth then two SOQL queries (accounts + opportunities)."""
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "access_token": "fake_token",
            "instance_url": "https://example.my.salesforce.com",
        },
    )
    mock_post.return_value.raise_for_status = lambda: None

    mock_get.side_effect = [
        # accounts response
        {
            "records": [
                {
                    "Id": "001ABC",
                    "Name": "Big Corp",
                    "Industry": "Tech",
                    "AnnualRevenue": 1000000.0,
                    "attributes": {"type": "Account"},
                }
            ],
            "done": True,
        },
        # opportunities response
        {
            "records": [
                {
                    "Id": "006XYZ",
                    "AccountId": "001ABC",
                    "Name": "Deal",
                    "Amount": 50000.0,
                    "StageName": "Closed Won",
                    "CloseDate": "2024-06-15",
                    "attributes": {"type": "Opportunity"},
                }
            ],
            "done": True,
        },
    ]

    ex = SalesforceExtractor()
    records = list(ex.extract(since=None))

    types = [r["_type"] for r in records]
    assert types == ["account", "opportunity"]

    # attributes must be stripped
    for r in records:
        assert "attributes" not in r

    assert records[0]["Id"] == "001ABC"
    assert records[1]["Id"] == "006XYZ"
    mock_post.assert_called_once()