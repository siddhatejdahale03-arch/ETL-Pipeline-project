"""Tests for the cleaner and mapper transform steps."""
import pytest

from src.transformers.cleaner import (
    clean_salesforce_accounts,
    clean_salesforce_opportunities,
    clean_stripe_charges,
    clean_stripe_customers,
    to_usd,
)
from src.transformers.mapper import (
    CUSTOMER_COLUMNS,
    TRANSACTION_COLUMNS,
    to_unified_customers,
    to_unified_transactions,
)


def test_stripe_customer_email_is_trimmed_and_lowercased():
    """Leading/trailing spaces and uppercase letters must be fixed."""
    df = clean_stripe_customers([
        {"id": "cus_1", "email": "  Alice@Example.COM ", "name": " Alice ", "created": 1700000000},
    ])
    row = df.to_dicts()[0]
    assert row["email"] == "alice@example.com"   # trimmed + lowercased
    assert row["full_name"] == "Alice"            # trimmed
    assert str(row["created_at"].tzinfo) == "UTC"  # must be timezone-aware


def test_bad_stripe_record_without_created_is_skipped():
    """A record missing the required 'created' field must be dropped silently."""
    df = clean_stripe_customers([
        {"id": "cus_1", "created": 1700000000},  # valid
        {"id": "cus_2"},                          # missing 'created' -> invalid
    ])
    assert df.height == 1


def test_stripe_charge_cents_converted_to_dollars():
    """Stripe stores amounts in cents — the cleaner must convert to dollars."""
    df = clean_stripe_charges([
        {"id": "ch_1", "amount": 1999, "currency": "usd", "status": "SUCCEEDED", "created": 1700000000},
        {"id": "ch_2", "amount": 10000, "currency": "eur", "status": "failed", "created": 1700000000},
    ])
    rows = df.to_dicts()
    assert rows[0]["amount_usd"] == 19.99       # 1999 cents -> $19.99
    assert rows[0]["status"] == "succeeded"     # status must be lowercased
    assert rows[1]["amount_usd"] == 108.0       # 100 EUR * 1.08 exchange rate


def test_unknown_currency_raises_value_error():
    """An unrecognised currency code must raise ValueError."""
    with pytest.raises(ValueError):
        to_usd(10, "xyz")


def test_salesforce_dates_converted_to_utc():
    """Salesforce dates with timezone offsets must be normalised to UTC."""
    df = clean_salesforce_accounts([{
        "Id": "001", "Name": "Acme",
        "CreatedDate": "2026-09-10T10:00:00.000+0530",   # IST = UTC+5:30
        "LastModifiedDate": "2026-09-11T10:00:00.000+0000",
    }])
    created = df.to_dicts()[0]["created_at"]
    assert str(created.tzinfo) == "UTC"
    assert created.hour == 4 and created.minute == 30  # 10:00 IST = 04:30 UTC


def test_unified_customers_have_correct_columns_for_both_sources():
    """After merging, the DataFrame must have exactly the unified schema columns."""
    stripe = clean_stripe_customers([{"id": "cus_1", "email": "a@b.com", "created": 1700000000}])
    sf = clean_salesforce_accounts([{
        "Id": "001", "Name": "Acme", "Industry": "Tech",
        "CreatedDate": "2026-09-10T10:00:00Z", "LastModifiedDate": "2026-09-10T10:00:00Z",
    }])

    unified = to_unified_customers(stripe, sf)

    assert unified.columns == CUSTOMER_COLUMNS
    assert sorted(unified["source_system"].to_list()) == ["salesforce", "stripe"]


def test_unified_transactions_deduplicate_same_id():
    """Duplicate records for the same (id, source) must be removed."""
    charge = {"id": "ch_1", "amount": 100, "currency": "usd", "status": "ok", "created": 1700000000}
    stripe = clean_stripe_charges([charge, charge])  # same charge twice
    sf = clean_salesforce_opportunities([
        {"Id": "006", "Amount": None, "StageName": "Closed Won", "CloseDate": "2026-10-01"},
    ])

    unified = to_unified_transactions(stripe, sf)

    assert unified.columns == TRANSACTION_COLUMNS
    assert unified.height == 2  # 1 unique Stripe charge + 1 Salesforce opportunity
