"""Unit tests for cleaner + mapper."""
import polars as pl

from src.transformers.cleaner import (
    cents_to_usd,
    clean_string,
    unix_to_datetime,
    clean_stripe_customers,
    clean_stripe_charges,
    clean_salesforce_accounts,
    clean_salesforce_opportunities,
)
from src.transformers.mapper import (
    to_unified_customers,
    to_unified_transactions,
)


def test_cents_to_usd():
    assert cents_to_usd(1000) == 10.0
    assert cents_to_usd(2550) == 25.5
    assert cents_to_usd(None) == 0.0
    assert cents_to_usd(0) == 0.0


def test_clean_string():
    assert clean_string("  hello ") == "hello"
    assert clean_string("") is None
    assert clean_string("   ") is None
    assert clean_string(None) is None


def test_unix_to_datetime():
    dt = unix_to_datetime(1700000000)
    assert dt is not None
    assert dt.year == 2023
    assert dt.tzinfo is not None


def test_unix_to_datetime_none():
    assert unix_to_datetime(None) is None


def test_clean_stripe_customers():
    raw = [
        {
            "id": "cus_1",
            "email": "a@b.com",
            "name": "Alice",
            "created": 1700000000,
            "delinquent": False,
        },
        {
            "id": "cus_2",
            "email": None,
            "name": None,
            "created": 1700000000,
            "delinquent": True,
        },
    ]
    df = clean_stripe_customers(raw)
    assert df.height == 2
    assert "customer_id" in df.columns
    assert df["is_delinquent"].to_list() == [False, True]
    assert df["customer_id"].to_list() == ["cus_1", "cus_2"]


def test_clean_stripe_customers_empty():
    df = clean_stripe_customers([])
    assert df.height == 0


def test_clean_stripe_charges():
    raw = [
        {
            "id": "ch_1",
            "customer": "cus_1",
            "amount": 2000,
            "currency": "usd",
            "status": "succeeded",
            "created": 1700000000,
            "description": "Test charge",
        }
    ]
    df = clean_stripe_charges(raw)
    assert df.height == 1
    assert df["amount_usd"][0] == 20.0
    assert df["status"][0] == "succeeded"


def test_clean_salesforce_accounts():
    raw = [
        {
            "Id": "001ABC",
            "Name": "Big Corp",
            "Industry": "Tech",
            "AnnualRevenue": 1000000.0,
            "CreatedDate": "2024-01-01T00:00:00Z",
            "LastModifiedDate": "2024-01-02T00:00:00Z",
        }
    ]
    df = clean_salesforce_accounts(raw)
    assert df.height == 1
    assert df["customer_id"][0] == "001ABC"
    assert df["industry"][0] == "Tech"


def test_clean_salesforce_opportunities():
    raw = [
        {
            "Id": "006XYZ",
            "AccountId": "001ABC",
            "Name": "Big Deal",
            "Amount": 50000.0,
            "StageName": "Closed Won",
            "CloseDate": "2024-06-15",
        }
    ]
    df = clean_salesforce_opportunities(raw)
    assert df.height == 1
    assert df["transaction_id"][0] == "006XYZ"
    assert df["amount_usd"][0] == 50000.0


def test_to_unified_customers_merges_sources():
    stripe_df = clean_stripe_customers(
        [
            {
                "id": "cus_1",
                "email": "a@b.com",
                "name": "Alice",
                "created": 1700000000,
                "delinquent": False,
            }
        ]
    )
    sf_df = pl.DataFrame(
        {
            "customer_id": ["001ABC"],
            "full_name": ["Big Corp"],
            "industry": ["Tech"],
            "annual_revenue_usd": [1_000_000.0],
            "created_at": ["2024-01-01T00:00:00Z"],
            "updated_at": ["2024-01-02T00:00:00Z"],
        }
    )
    unified = to_unified_customers(stripe_df, sf_df)
    assert unified.height == 2
    assert set(unified["source_system"].to_list()) == {"stripe", "salesforce"}
    assert "ingested_at" in unified.columns


def test_to_unified_transactions_empty():
    result = to_unified_transactions(pl.DataFrame(), pl.DataFrame())
    assert result.height == 0


def test_to_unified_transactions_merges():
    stripe_df = clean_stripe_charges(
        [
            {
                "id": "ch_1",
                "customer": "cus_1",
                "amount": 5000,
                "currency": "usd",
                "status": "succeeded",
                "created": 1700000000,
                "description": "Charge 1",
            }
        ]
    )
    sf_df = pl.DataFrame(
        {
            "transaction_id": ["006XYZ"],
            "customer_id": ["001ABC"],
            "amount_usd": [50000.0],
            "status": ["Closed Won"],
            "description": ["Big Deal"],
            "occurred_at": ["2024-06-15"],
        }
    )
    unified = to_unified_transactions(stripe_df, sf_df)
    assert unified.height == 2
    assert set(unified["source_system"].to_list()) == {"stripe", "salesforce"}