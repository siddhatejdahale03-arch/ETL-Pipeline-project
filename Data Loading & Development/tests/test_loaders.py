"""Unit tests for src.loaders.db_loader.DBLoader."""
from datetime import datetime, timezone

import polars as pl
import pytest
from sqlalchemy import text

from src.loaders.db_loader import DBLoader


@pytest.fixture(scope="module")
def loader():
    """Shared DBLoader instance for all tests."""
    return DBLoader()


@pytest.fixture(autouse=True)
def clean_tables(loader):
    """Wipe tables before each test so runs are isolated."""
    loader.ensure_schema()
    with loader.engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE customers RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE TABLE transactions RESTART IDENTITY CASCADE"))
    yield


def _customers_df(rows=1):
    """Build a minimal customers DataFrame."""
    now = datetime.now(timezone.utc)
    return pl.DataFrame({
        "customer_id":   [f"cust_{i}" for i in range(rows)],
        "source_system": ["stripe"] * rows,
        "email":         [f"user{i}@example.com" for i in range(rows)],
        "full_name":     [f"User {i}" for i in range(rows)],
        "industry":      ["Technology"] * rows,
        "annual_revenue_usd": [1000000.0] * rows,
        "is_delinquent": [False] * rows,
        "created_at":    [now] * rows,
        "updated_at":    [now] * rows,
        "ingested_at":   [now] * rows,
    })


def test_upsert_inserts_new_row(loader):
    df = _customers_df(1)
    n = loader.upsert("customers", df, ["customer_id", "source_system"])
    assert n == 1
    assert loader.fetch_count("customers") == 1


def test_upsert_empty_df_returns_zero(loader):
    empty = _customers_df(0)
    n = loader.upsert("customers", empty, ["customer_id", "source_system"])
    assert n == 0
    assert loader.fetch_count("customers") == 0


def test_upsert_updates_existing_row(loader):
    df = _customers_df(1)
    loader.upsert("customers", df, ["customer_id", "source_system"])
    assert loader.fetch_count("customers") == 1
    df_updated = df.with_columns(pl.lit("newemail@example.com").alias("email"))
    loader.upsert("customers", df_updated, ["customer_id", "source_system"])
    assert loader.fetch_count("customers") == 1
    with loader.engine.begin() as conn:
        email = conn.execute(
            text("SELECT email FROM customers WHERE customer_id = 'cust_0'")
        ).scalar()
    assert email == "newemail@example.com"


def test_upsert_multiple_rows(loader):
    df = _customers_df(5)
    n = loader.upsert("customers", df, ["customer_id", "source_system"])
    assert n == 5
    assert loader.fetch_count("customers") == 5


def test_fetch_count_empty_table(loader):
    assert loader.fetch_count("customers") == 0
    assert loader.fetch_count("transactions") == 0


def test_upsert_transactions(loader):
    now = datetime.now(timezone.utc)
    df = pl.DataFrame({
        "transaction_id": ["tx_001"],
        "source_system":  ["stripe"],
        "customer_id":    ["cust_0"],
        "amount_usd":     [99.99],
        "status":         ["succeeded"],
        "description":    ["Test charge"],
        "occurred_at":    [now],
        "ingested_at":    [now],
    })
    n = loader.upsert("transactions", df, ["transaction_id", "source_system"])
    assert n == 1
    assert loader.fetch_count("transactions") == 1


def test_ensure_schema_idempotent(loader):
    loader.ensure_schema()
    loader.ensure_schema()
    assert loader.fetch_count("customers") == 0
