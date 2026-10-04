"""Tests for cleaning and mapping."""
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


def test_stripe_customer_is_cleaned():
    df = clean_stripe_customers([
        {"id": "cus_1", "email": "  Alice@Example.COM ", "name": " Alice ", "created": 1700000000},
    ])
    row = df.to_dicts()[0]
    assert row["email"] == "alice@example.com"   # trimmed + lowercase
    assert row["full_name"] == "Alice"
    assert str(row["created_at"].tzinfo) == "UTC"


def test_bad_record_is_skipped():
    df = clean_stripe_customers([
        {"id": "cus_1", "created": 1700000000},
        {"id": "cus_2"},  # missing "created" -> invalid
    ])
    assert df.height == 1


def test_charge_cents_to_dollars_and_currency():
    df = clean_stripe_charges([
        {"id": "ch_1", "amount": 1999, "currency": "usd", "status": "SUCCEEDED", "created": 1700000000},
        {"id": "ch_2", "amount": 10000, "currency": "eur", "status": "failed", "created": 1700000000},
    ])
    rows = df.to_dicts()
    assert rows[0]["amount_usd"] == 19.99
    assert rows[0]["status"] == "succeeded"
    assert rows[1]["amount_usd"] == 108.0  # 100 EUR * 1.08


def test_unknown_currency_raises():
    with pytest.raises(ValueError):
        to_usd(10, "xyz")


def test_salesforce_dates_become_utc():
    df = clean_salesforce_accounts([{
        "Id": "001", "Name": "Acme", "CreatedDate": "2026-09-10T10:00:00.000+0530",
        "LastModifiedDate": "2026-09-11T10:00:00.000+0000",
    }])
    created = df.to_dicts()[0]["created_at"]
    assert str(created.tzinfo) == "UTC"
    assert created.hour == 4 and created.minute == 30  # 10:00 IST = 04:30 UTC


def test_unified_customers_have_same_columns_for_both_sources():
    stripe = clean_stripe_customers([{"id": "cus_1", "email": "a@b.com", "created": 1700000000}])
    sf = clean_salesforce_accounts([{
        "Id": "001", "Name": "Acme", "Industry": "Tech",
        "CreatedDate": "2026-09-10T10:00:00Z", "LastModifiedDate": "2026-09-10T10:00:00Z",
    }])

    unified = to_unified_customers(stripe, sf)

    assert unified.columns == CUSTOMER_COLUMNS
    assert sorted(unified["source_system"].to_list()) == ["salesforce", "stripe"]


def test_unified_transactions_remove_duplicates():
    charge = {"id": "ch_1", "amount": 100, "currency": "usd", "status": "ok", "created": 1700000000}
    stripe = clean_stripe_charges([charge, charge])  # same charge twice
    sf = clean_salesforce_opportunities([
        {"Id": "006", "Amount": None, "StageName": "Closed Won", "CloseDate": "2026-10-01"},
    ])

    unified = to_unified_transactions(stripe, sf)

    assert unified.columns == TRANSACTION_COLUMNS
    assert unified.height == 2
