"""
tests/test_transformer.py — Tests for the end-to-end transform pipeline.

Updated to use the new pipeline:
  clean_stripe_customers() -> to_unified_customers()
instead of the removed transform_customer() function.
"""
from src.transformers.cleaner import clean_stripe_customers, clean_salesforce_accounts
from src.transformers.mapper import to_unified_customers, CUSTOMER_COLUMNS


def test_transform_pipeline_cleans_and_unifies():
    """
    Full transform: raw Stripe dict -> cleaned DataFrame -> unified DataFrame.
    Replaces the old transform_customer() test.
    """
    raw = [{"id": "cus_123", "name": "  Alice Johnson  ",
            "email": " Alice@Example.COM ", "currency": "USD", "created": 0}]

    cleaned = clean_stripe_customers(raw)
    unified = to_unified_customers(cleaned, None)

    row = unified.to_dicts()[0]
    assert row["customer_id"] == "cus_123"
    assert row["full_name"] == "Alice Johnson"        # trimmed
    assert row["email"] == "alice@example.com"        # trimmed + lowercased
    assert row["source_system"] == "stripe"


def test_transform_pipeline_produces_correct_columns():
    """Unified output must always have exactly the defined schema columns."""
    raw = [{"id": "cus_1", "email": "a@b.com", "created": 1700000000}]
    cleaned = clean_stripe_customers(raw)
    unified = to_unified_customers(cleaned, None)
    assert unified.columns == CUSTOMER_COLUMNS


def test_transform_pipeline_handles_null_email():
    """A customer with no email must still produce a valid unified row."""
    raw = [{"id": "cus_no_email", "email": None, "created": 1700000000}]
    cleaned = clean_stripe_customers(raw)
    unified = to_unified_customers(cleaned, None)
    assert unified.to_dicts()[0]["email"] is None


def test_transform_merges_stripe_and_salesforce():
    """Stripe + Salesforce records must appear together in the unified table."""
    stripe_raw = [{"id": "cus_stripe", "email": "s@s.com", "created": 1700000000}]
    sf_raw = [{
        "Id": "sf_001", "Name": "Acme",
        "CreatedDate": "2026-09-10T10:00:00Z",
        "LastModifiedDate": "2026-09-10T10:00:00Z",
    }]

    stripe_df = clean_stripe_customers(stripe_raw)
    sf_df = clean_salesforce_accounts(sf_raw)
    unified = to_unified_customers(stripe_df, sf_df)

    sources = sorted(unified["source_system"].to_list())
    assert sources == ["salesforce", "stripe"]
    assert unified.height == 2