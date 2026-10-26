"""
Step 1 of TRANSFORM: clean the raw API records.

For every source we:
    1. Check the record with its Pydantic model (bad records are skipped)
    2. Rename fields to our internal names
    3. Fix formats: Unix time -> UTC datetime, cents -> dollars,
       other currencies -> USD, trim spaces, lowercase emails
    4. Return a Polars DataFrame
"""
from datetime import datetime, time, timezone

import polars as pl
from pydantic import ValidationError

from src.models.source_models import (
    SalesforceAccount,
    SalesforceOpportunity,
    StripeCharge,
    StripeCustomer,
)
from src.utils.logger import get_logger

log = get_logger("cleaner")

# Simple fixed exchange rates (to USD). In a real company these would come from an API.
USD_RATES = {"usd": 1.0, "eur": 1.08, "gbp": 1.27, "inr": 0.012}


# ---------------- small helper functions ----------------
def clean_text(value):
    """Trim leading/trailing whitespace. Empty strings become None."""
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def clean_email(value):
    """Trim and lowercase an email address. Returns None if empty."""
    value = clean_text(value)
    return value.lower() if value else None


def unix_to_utc(seconds: int) -> datetime:
    """Convert a Unix timestamp (seconds) to a timezone-aware UTC datetime."""
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def to_utc(value: datetime) -> datetime:
    """Make sure a datetime is in UTC (add UTC info if naive)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_usd(amount: float, currency: str) -> float:
    """Convert amount in given currency to USD using fixed rates."""
    rate = USD_RATES.get(currency.lower())
    if rate is None:
        raise ValueError(f"Unknown currency: {currency}")
    return round(amount * rate, 2)


def validate(records: list[dict], model) -> list:
    """
    Turn each dict into a Pydantic model instance.

    Bad records (missing required fields, wrong types) are logged
    and skipped so one bad row doesn't crash the whole pipeline.
    """
    good = []
    for record in records:
        try:
            good.append(model(**record))
        except ValidationError as error:
            log.warning("bad_record_skipped", model=model.__name__,
                        id=record.get("id") or record.get("Id"), errors=error.error_count())
    return good


# ---------------- Stripe ----------------
def clean_stripe_customers(records: list[dict]) -> pl.DataFrame:
    """Validate and clean raw Stripe customer records into a DataFrame."""
    rows = []
    for c in validate(records, StripeCustomer):
        rows.append({
            "customer_id": c.id,
            "email": clean_email(c.email),
            "full_name": clean_text(c.name),
            "is_delinquent": c.delinquent,
            "created_at": unix_to_utc(c.created),
            "updated_at": unix_to_utc(c.created),  # Stripe has no "updated" field
        })
    log.info("cleaned", source="stripe_customers", rows=len(rows))
    return pl.DataFrame(rows)


def clean_stripe_charges(records: list[dict]) -> pl.DataFrame:
    """Validate and clean raw Stripe charge records. Converts cents -> dollars."""
    rows = []
    for ch in validate(records, StripeCharge):
        try:
            amount_usd = to_usd(ch.amount / 100, ch.currency)  # Stripe stores cents
        except ValueError as error:
            log.warning("bad_record_skipped", id=ch.id, error=error)
            continue
        rows.append({
            "transaction_id": ch.id,
            "customer_id": ch.customer,
            "amount_usd": amount_usd,
            "status": ch.status.lower(),
            "description": clean_text(ch.description),
            "occurred_at": unix_to_utc(ch.created),
        })
    log.info("cleaned", source="stripe_charges", rows=len(rows))
    return pl.DataFrame(rows)


# ---------------- Salesforce ----------------
def clean_salesforce_accounts(records: list[dict]) -> pl.DataFrame:
    """Validate and clean raw Salesforce Account records."""
    rows = []
    for a in validate(records, SalesforceAccount):
        rows.append({
            "customer_id": a.Id,
            "full_name": clean_text(a.Name),
            "industry": clean_text(a.Industry),
            "annual_revenue_usd": a.AnnualRevenue,
            "created_at": to_utc(a.CreatedDate),
            "updated_at": to_utc(a.LastModifiedDate),
        })
    log.info("cleaned", source="salesforce_accounts", rows=len(rows))
    return pl.DataFrame(rows)


def clean_salesforce_opportunities(records: list[dict]) -> pl.DataFrame:
    """Validate and clean raw Salesforce Opportunity records."""
    rows = []
    for o in validate(records, SalesforceOpportunity):
        rows.append({
            "transaction_id": o.Id,
            "customer_id": o.AccountId,
            "amount_usd": o.Amount or 0.0,  # missing amount defaults to 0
            "status": o.StageName.lower(),
            "description": clean_text(o.Name),
            # CloseDate is a date, combine with midnight to make a datetime
            "occurred_at": datetime.combine(o.CloseDate, time(0, 0), tzinfo=timezone.utc),
        })
    log.info("cleaned", source="salesforce_opportunities", rows=len(rows))
    return pl.DataFrame(rows)