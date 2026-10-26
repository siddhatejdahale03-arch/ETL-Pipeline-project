"""
Step 2 of TRANSFORM: put Stripe + Salesforce data into ONE unified table.

    Stripe customers  ┐
                      ├──>  customers     (same columns for both sources)
    SF accounts       ┘

    Stripe charges    ┐
                      ├──>  transactions
    SF opportunities  ┘
"""
from datetime import datetime, timezone

import polars as pl

from src.models.unified_models import UnifiedCustomer, UnifiedTransaction
from src.utils.logger import get_logger

log = get_logger("mapper")

# Fixed column order — same as the Pydantic model field definitions
CUSTOMER_COLUMNS = list(UnifiedCustomer.model_fields)
TRANSACTION_COLUMNS = list(UnifiedTransaction.model_fields)


def _unify(frames: dict[str, pl.DataFrame], model, columns: list[str], key: str) -> pl.DataFrame:
    """
    Merge DataFrames from multiple sources into one unified DataFrame.

    frames = {"stripe": df1, "salesforce": df2}

    Steps:
    1. Add source_system and ingested_at to every row
    2. Check each row against the unified Pydantic model (fills defaults)
    3. Remove duplicates (same id + same source)
    4. Return one DataFrame with columns in a fixed order
    """
    now = datetime.now(timezone.utc)
    rows = []
    for source, df in frames.items():
        if df is None or df.height == 0:
            continue  # skip empty DataFrames
        for row in df.to_dicts():
            row["source_system"] = source
            row["ingested_at"] = now
            rows.append(model(**row).model_dump())  # fills missing columns with defaults

    if not rows:
        return pl.DataFrame()

    unified = pl.DataFrame(rows).select(columns)
    # Keep the most recent record when a (id, source) pair appears more than once
    unified = unified.unique(subset=[key, "source_system"], keep="last", maintain_order=True)
    log.info("unified", table=model.__name__, rows=unified.height)
    return unified


def to_unified_customers(stripe_df: pl.DataFrame, sf_df: pl.DataFrame) -> pl.DataFrame:
    """Merge Stripe customers + Salesforce accounts into one customers DataFrame."""
    return _unify({"stripe": stripe_df, "salesforce": sf_df},
                  UnifiedCustomer, CUSTOMER_COLUMNS, "customer_id")


def to_unified_transactions(stripe_df: pl.DataFrame, sf_df: pl.DataFrame) -> pl.DataFrame:
    """Merge Stripe charges + Salesforce opportunities into one transactions DataFrame."""
    return _unify({"stripe": stripe_df, "salesforce": sf_df},
                  UnifiedTransaction, TRANSACTION_COLUMNS, "transaction_id")