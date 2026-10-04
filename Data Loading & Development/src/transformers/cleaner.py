"""Polars-based cleaning utilities."""
from datetime import datetime, timezone

import polars as pl

from src.utils.logger import get_logger

log = get_logger("cleaner")


def unix_to_datetime(ts: int | float | None) -> datetime | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(float(ts), tz=timezone.utc)


def clean_string(value: str | None) -> str | None:
    if value is None:
        return None
    v = str(value).strip()
    return v or None


def cents_to_usd(cents: int | float | None) -> float:
    if cents is None:
        return 0.0
    return round(float(cents) / 100.0, 2)


def clean_stripe_customers(records: list[dict]) -> pl.DataFrame:
    if not records:
        return pl.DataFrame()
    rows = []
    for r in records:
        rows.append(
            {
                "customer_id": r["id"],
                "email": clean_string(r.get("email")),
                "full_name": clean_string(r.get("name")),
                "created_at": unix_to_datetime(r.get("created")),
                "is_delinquent": bool(r.get("delinquent", False)),
            }
        )
    df = pl.DataFrame(rows).drop_nulls(subset=["customer_id"])
    log.info("cleaned_stripe_customers", rows=df.height)
    return df


def clean_stripe_charges(records: list[dict]) -> pl.DataFrame:
    if not records:
        return pl.DataFrame()
    rows = []
    for r in records:
        rows.append(
            {
                "transaction_id": r["id"],
                "customer_id": r.get("customer"),
                "amount_usd": cents_to_usd(r.get("amount")),
                "status": r.get("status", "unknown"),
                "description": clean_string(r.get("description")),
                "occurred_at": unix_to_datetime(r.get("created")),
            }
        )
    df = pl.DataFrame(rows)
    log.info("cleaned_stripe_charges", rows=df.height)
    return df


def clean_salesforce_accounts(records: list[dict]) -> pl.DataFrame:
    if not records:
        return pl.DataFrame()
    rows = []
    for r in records:
        rows.append(
            {
                "customer_id": r["Id"],
                "full_name": clean_string(r.get("Name")),
                "industry": clean_string(r.get("Industry")),
                "annual_revenue_usd": float(r["AnnualRevenue"])
                if r.get("AnnualRevenue")
                else None,
                "created_at": r.get("CreatedDate"),
                "updated_at": r.get("LastModifiedDate"),
            }
        )
    return pl.DataFrame(rows)


def clean_salesforce_opportunities(records: list[dict]) -> pl.DataFrame:
    if not records:
        return pl.DataFrame()
    rows = []
    for r in records:
        rows.append(
            {
                "transaction_id": r["Id"],
                "customer_id": r.get("AccountId"),
                "amount_usd": float(r["Amount"]) if r.get("Amount") else 0.0,
                "status": r.get("StageName", "unknown"),
                "description": clean_string(r.get("Name")),
                "occurred_at": r.get("CloseDate"),
            }
        )
    return pl.DataFrame(rows)