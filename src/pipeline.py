"""
The complete ETL pipeline in one function: run_pipeline().

    EXTRACT    Stripe + Salesforce APIs  ->  raw records
    SAVE RAW   raw records               ->  S3 (or data/raw/)
    TRANSFORM  clean + map               ->  unified customers / transactions
    LOAD       upsert                    ->  PostgreSQL data warehouse

Run it by hand:   python -m src.pipeline
Airflow runs it:  dags/etl_dag.py
"""
from datetime import datetime, timedelta, timezone

from config.settings import PROJECT_ROOT, get_settings
from src.extractors.salesforce_extractor import SalesforceExtractor
from src.extractors.stripe_extractor import StripeExtractor
from src.loaders.db_loader import DBLoader
from src.loaders.s3_loader import S3Loader
from src.transformers.cleaner import (
    clean_salesforce_accounts,
    clean_salesforce_opportunities,
    clean_stripe_charges,
    clean_stripe_customers,
)
from src.transformers.mapper import to_unified_customers, to_unified_transactions
from src.utils.alerts import send_slack_alert
from src.utils.logger import get_logger

log = get_logger("pipeline")

# Path to the SQL file that creates the warehouse tables
SCHEMA_FILE = PROJECT_ROOT / "sql" / "schema.sql"


def only_type(records: list[dict], record_type: str) -> list[dict]:
    """
    Filter records by their '_type' tag.

    The extractors tag each record with a '_type' so we know which
    transformer to use without needing separate API calls.
    e.g. only_type(stripe_records, "customer")
    """
    return [r for r in records if r["_type"] == record_type]


def run_pipeline(incremental: bool = True) -> dict:
    """
    Run the full ETL pipeline and return a summary dict.

    Args:
        incremental: True  -> only fetch data from the last 24 hours (daily run)
                     False -> fetch everything (first run / full reload)

    Returns:
        dict with counts: stripe_raw, salesforce_raw, customers_loaded, transactions_loaded
    """
    # Incremental mode: only process records changed in the last 24h
    since = None
    if incremental and not get_settings().demo_mode:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
    log.info("pipeline_start", incremental=incremental, since=since)

    # ======================== EXTRACT ========================
    # Pull raw data from both sources
    stripe_records = StripeExtractor().extract(since=since)
    sf_records = SalesforceExtractor().extract(since=since)

    # Save raw data to S3 or local disk BEFORE any transformation
    # This gives us a "data lake" — we can re-process without calling APIs again
    raw_store = S3Loader()
    raw_store.write_json("stripe", stripe_records)
    raw_store.write_json("salesforce", sf_records)

    # ======================== TRANSFORM ========================
    # Clean each type separately, then unify into shared schema
    stripe_customers = clean_stripe_customers(only_type(stripe_records, "customer"))
    stripe_charges = clean_stripe_charges(only_type(stripe_records, "charge"))
    sf_accounts = clean_salesforce_accounts(only_type(sf_records, "account"))
    sf_opps = clean_salesforce_opportunities(only_type(sf_records, "opportunity"))

    # Merge Stripe + Salesforce into unified tables
    unified_customers = to_unified_customers(stripe_customers, sf_accounts)
    unified_tx = to_unified_transactions(stripe_charges, sf_opps)

    # ======================== LOAD ========================
    # Rohan's DBLoader: create tables if missing, then upsert rows
    loader = DBLoader()
    loader.ensure_schema(str(SCHEMA_FILE))
    n_customers = loader.upsert("customers", unified_customers, ["customer_id", "source_system"])
    n_tx = loader.upsert("transactions", unified_tx, ["transaction_id", "source_system"])

    summary = {
        "stripe_raw": len(stripe_records),
        "salesforce_raw": len(sf_records),
        "customers_loaded": n_customers,
        "transactions_loaded": n_tx,
    }
    log.info("pipeline_complete", **summary)

    # Notify the team when a full reload finishes (not every incremental run)
    if not incremental:
        send_slack_alert(f"Full ETL reload complete: {summary}")
    return summary


if __name__ == "__main__":
    # Quick test: run a full reload and print the summary
    print(run_pipeline(incremental=False))
