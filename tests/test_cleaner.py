"""
tests/test_cleaner.py — Tests for the cleaner transformer.

Updated to use the new multi-source cleaner functions (Stripe + Salesforce).
Old function: clean_customer_data() — removed in final integration.
New functions: clean_stripe_customers(), clean_stripe_charges(), etc.
"""
from src.transformers.cleaner import (
    clean_stripe_customers,
    clean_stripe_charges,
    clean_salesforce_accounts,
    clean_text,
    clean_email,
)


def test_clean_stripe_customer_trims_name_and_email():
    """Leading/trailing whitespace must be stripped from name and email."""
    df = clean_stripe_customers([
        {"id": "cus_123", "name": "  Alice Johnson  ", "email": " alice@example.com ", "created": 1700000000}
    ])
    row = df.to_dicts()[0]
    assert row["full_name"] == "Alice Johnson"
    assert row["email"] == "alice@example.com"


def test_clean_stripe_customer_blank_name_becomes_none():
    """A name that is only whitespace must be converted to None."""
    df = clean_stripe_customers([
        {"id": "cus_123", "name": "   ", "created": 1700000000}
    ])
    row = df.to_dicts()[0]
    assert row["full_name"] is None


def test_clean_stripe_customer_email_is_lowercased():
    """Email addresses must always be stored in lowercase."""
    df = clean_stripe_customers([
        {"id": "cus_1", "email": "ALICE@EXAMPLE.COM", "created": 1700000000}
    ])
    assert df.to_dicts()[0]["email"] == "alice@example.com"


def test_clean_stripe_customer_null_email_stays_none():
    """A null email from the API must remain None (not become the string 'None')."""
    df = clean_stripe_customers([
        {"id": "cus_1", "email": None, "created": 1700000000}
    ])
    assert df.to_dicts()[0]["email"] is None


def test_clean_stripe_charge_converts_cents_to_dollars():
    """Stripe stores amounts in cents — cleaner must divide by 100."""
    df = clean_stripe_charges([
        {"id": "ch_1", "amount": 4999, "currency": "usd", "status": "succeeded", "created": 1700000000}
    ])
    assert df.to_dicts()[0]["amount_usd"] == 49.99


def test_clean_stripe_charge_status_is_lowercased():
    """Charge status must be lowercase regardless of what Stripe sends."""
    df = clean_stripe_charges([
        {"id": "ch_1", "amount": 100, "currency": "usd", "status": "SUCCEEDED", "created": 1700000000}
    ])
    assert df.to_dicts()[0]["status"] == "succeeded"


def test_clean_salesforce_account_trims_name():
    """Salesforce account name must be trimmed."""
    df = clean_salesforce_accounts([{
        "Id": "001",
        "Name": "  Acme Corp  ",
        "CreatedDate": "2026-09-10T10:00:00Z",
        "LastModifiedDate": "2026-09-10T10:00:00Z",
    }])
    assert df.to_dicts()[0]["full_name"] == "Acme Corp"


def test_clean_text_helper_trims_whitespace():
    """clean_text() helper must strip spaces and return None for blank strings."""
    assert clean_text("  hello  ") == "hello"
    assert clean_text("   ") is None
    assert clean_text(None) is None


def test_clean_email_helper_lowercases():
    """clean_email() helper must trim and lowercase."""
    assert clean_email("  Alice@EXAMPLE.com  ") == "alice@example.com"
    assert clean_email(None) is None