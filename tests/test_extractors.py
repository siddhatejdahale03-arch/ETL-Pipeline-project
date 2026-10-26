"""Tests for the Stripe and Salesforce extractors in demo mode."""
from unittest.mock import patch

from src.extractors.salesforce_extractor import SalesforceExtractor
from src.extractors.stripe_extractor import StripeExtractor


def test_stripe_extractor_returns_tagged_records_in_demo_mode():
    """In DEMO_MODE, the extractor must read sample files and tag records correctly."""
    extractor = StripeExtractor()
    records = extractor.extract()

    # Every record must have a _type tag
    types = {r["_type"] for r in records}
    assert "customer" in types
    assert "charge" in types

    # Customer records must have an 'id' field
    customers = [r for r in records if r["_type"] == "customer"]
    assert all("id" in r for r in customers)


def test_salesforce_extractor_returns_tagged_records_in_demo_mode():
    """In DEMO_MODE, the Salesforce extractor must read sample files and tag records."""
    extractor = SalesforceExtractor()
    records = extractor.extract()

    types = {r["_type"] for r in records}
    assert "account" in types
    assert "opportunity" in types

    # Account records must have the Salesforce 'Id' field (capital I)
    accounts = [r for r in records if r["_type"] == "account"]
    assert all("Id" in r for r in accounts)
