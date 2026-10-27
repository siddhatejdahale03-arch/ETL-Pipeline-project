"""
tests/test_stripe_extractor.py — Tests for StripeExtractor.

Updated for the new StripeExtractor that:
  - reads api_key from config/settings.py (not a constructor arg)
  - uses demo_mode=True to avoid real API calls in tests
  - tags records with '_type': 'customer' or 'charge'
"""
from unittest.mock import patch

from src.extractors.stripe_extractor import StripeExtractor


class TestStripeExtractorDemoMode:
    """In DEMO_MODE the extractor reads from data/sample/ — no API needed."""

    def test_extract_returns_both_customers_and_charges(self):
        """extract() must return a mix of customer and charge records."""
        extractor = StripeExtractor()
        records = extractor.extract()

        types = {r["_type"] for r in records}
        assert "customer" in types
        assert "charge" in types

    def test_all_records_have_type_tag(self):
        """Every record must have a '_type' key set by the extractor."""
        extractor = StripeExtractor()
        records = extractor.extract()
        assert all("_type" in r for r in records)

    def test_customer_records_have_id(self):
        """Customer records from sample data must all have an 'id' field."""
        extractor = StripeExtractor()
        customers = [r for r in extractor.extract() if r["_type"] == "customer"]
        assert len(customers) > 0
        assert all("id" in r for r in customers)

    def test_charge_records_have_amount(self):
        """Charge records from sample data must all have an 'amount' field."""
        extractor = StripeExtractor()
        charges = [r for r in extractor.extract() if r["_type"] == "charge"]
        assert len(charges) > 0
        assert all("amount" in r for r in charges)

    def test_returns_list(self):
        """extract() must always return a list, never None."""
        extractor = StripeExtractor()
        result = extractor.extract()
        assert isinstance(result, list)


class TestStripeExtractorPagination:
    """Test that the live pagination logic handles multiple pages correctly."""

    def test_fetch_all_follows_has_more(self):
        """fetch_all() must keep requesting pages while 'has_more' is True."""
        extractor = StripeExtractor()

        page1 = {"data": [{"id": "cus_1"}, {"id": "cus_2"}], "has_more": True}
        page2 = {"data": [{"id": "cus_3"}], "has_more": False}

        call_count = {"n": 0}

        def fake_get_json(url, headers, params=None):
            call_count["n"] += 1
            return page1 if call_count["n"] == 1 else page2

        with patch("src.extractors.stripe_extractor.get_json", side_effect=fake_get_json):
            records = extractor.fetch_all("customers")

        assert len(records) == 3
        assert call_count["n"] == 2   # exactly 2 API calls made

    def test_fetch_all_stops_when_no_more(self):
        """fetch_all() must stop immediately when 'has_more' is False."""
        extractor = StripeExtractor()
        single_page = {"data": [{"id": "cus_only"}], "has_more": False}

        with patch("src.extractors.stripe_extractor.get_json", return_value=single_page):
            records = extractor.fetch_all("customers")

        assert len(records) == 1
