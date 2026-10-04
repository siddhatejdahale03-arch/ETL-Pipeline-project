"""End-to-end ETL pipeline orchestrator."""
from datetime import datetime, timedelta, timezone

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


def _incremental_since(hours: int = 24) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_pipeline(incremental: bool = True) -> dict:
    """Run full ETL: Extract → S3 → Transform → Upsert DW."""
    since = _incremental_since() if incremental else None
    s3 = S3Loader()

    # ---------- EXTRACT ----------
    log.info("extract_phase_start", since=since)
    stripe_records = list(StripeExtractor().extract(since=since))
    sf_records = list(SalesforceExtractor().extract(since=since))

    s3.write_json("stripe", stripe_records)
    s3.write_json("salesforce", sf_records)

    # ---------- TRANSFORM ----------
    log.info("transform_phase_start")
    stripe_customers = clean_stripe_customers(
        [r for r in stripe_records if r["_type"] == "customer"]
    )
    stripe_charges = clean_stripe_charges(
        [r for r in stripe_records if r["_type"] == "charge"]
    )
    sf_accounts = clean_salesforce_accounts(
        [r for r in sf_records if r["_type"] == "account"]
    )
    sf_opps = clean_salesforce_opportunities(
        [r for r in sf_records if r["_type"] == "opportunity"]
    )

    unified_customers = to_unified_customers(stripe_customers, sf_accounts)
    unified_tx = to_unified_transactions(stripe_charges, sf_opps)

    # ---------- LOAD ----------
    log.info("load_phase_start")
    loader = DBLoader()
    loader.ensure_schema()
    n_customers = loader.upsert(
        "customers", unified_customers, ["customer_id", "source_system"]
    )
    n_tx = loader.upsert(
        "transactions", unified_tx, ["transaction_id", "source_system"]
    )

    summary = {
        "customers_loaded": n_customers,
        "transactions_loaded": n_tx,
        "stripe_raw": len(stripe_records),
        "salesforce_raw": len(sf_records),
    }
    log.info("pipeline_complete", **summary)

    if not incremental:
        send_slack_alert(f"✅ Full ETL complete: {summary}")

    return summary


if __name__ == "__main__":
    run_pipeline()