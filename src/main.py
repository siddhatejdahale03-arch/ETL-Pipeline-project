"""
main.py — ETL Pipeline Orchestrator (Week 1: Extract → Raw Store).

Automatically selects storage backend based on STORAGE_BACKEND env var:
  - "local"  → saves to local disk (default, free, no cloud needed)
  - "s3"     → uploads to AWS S3

Run:
    cd src
    python main.py
"""

import sys
import uuid
from datetime import datetime, timezone

from utils.logger import get_logger

logger = get_logger("etl.pipeline")


def _get_loader():
    """
    Factory: return the right loader based on STORAGE_BACKEND config.

    Returns LocalFileLoader by default (free, no cloud setup).
    Returns S3Loader when STORAGE_BACKEND=s3 (requires AWS credentials).
    """
    import config

    backend = config.STORAGE_BACKEND

    if backend == "s3":
        config._validate_s3_config()
        from loaders.s3_loader import S3Loader
        logger.info("Using S3 storage backend", extra={"bucket": config.AWS_BUCKET_NAME})
        return S3Loader()
    else:
        from loaders.local_loader import LocalFileLoader
        logger.info("Using local storage backend", extra={"path": config.LOCAL_STORAGE_PATH})
        return LocalFileLoader()


def run_pipeline() -> None:
    """
    Orchestrate the full Extract → Raw Store pipeline.

    Raises:
        ValueError:  If configuration is invalid (missing env vars).
        SystemExit:  On unrecoverable error (exits with code 1).
    """
    run_id = str(uuid.uuid4())
    started_at = datetime.now(tz=timezone.utc)

    logger.info(
        "Pipeline starting",
        extra={"run_id": run_id, "started_at": started_at.isoformat()},
    )

    # ------------------------------------------------------------------
    # 1. Validate config
    # ------------------------------------------------------------------
    try:
        import config
        logger.info(
            "Configuration validated",
            extra={"storage_backend": config.STORAGE_BACKEND},
        )
    except ValueError as exc:
        logger.error("Configuration error — aborting pipeline", extra={"error": str(exc)})
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Extract: Stripe Customers
    # ------------------------------------------------------------------
    from extractors.stripe_extractor import StripeExtractor

    logger.info("Starting extraction — Stripe customers", extra={"run_id": run_id})

    extractor = StripeExtractor(page_limit=config.STRIPE_PAGE_LIMIT)

    try:
        customers, extract_elapsed = extractor.extract_with_timing()
    except Exception as exc:
        logger.error(
            "Extraction failed — aborting pipeline",
            extra={"run_id": run_id, "error": str(exc)},
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Load: Save raw JSON to storage backend
    # ------------------------------------------------------------------
    try:
        loader = _get_loader()
    except ValueError as exc:
        logger.error("Storage config error", extra={"error": str(exc)})
        sys.exit(1)

    logger.info("Starting load phase", extra={"run_id": run_id})

    raw_records = [customer.model_dump() for customer in customers]

    try:
        data_location, manifest = loader.upload(
            source="stripe",
            entity="customers",
            records=raw_records,
            run_id=run_id,
            extracted_at=started_at,
        )
    except Exception as exc:
        logger.error(
            "Data store write failed — aborting pipeline",
            extra={"run_id": run_id, "error": str(exc)},
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # 4. Summary
    # ------------------------------------------------------------------
    finished_at = datetime.now(tz=timezone.utc)
    total_elapsed = round((finished_at - started_at).total_seconds(), 3)

    logger.info(
        "Pipeline complete",
        extra={
            "run_id": run_id,
            "status": "success",
            "total_elapsed_seconds": total_elapsed,
            "record_count": len(customers),
            "storage_backend": config.STORAGE_BACKEND,
            "data_location": data_location,
        },
    )

    # Human-readable summary
    storage_label = "📁 Local Path" if config.STORAGE_BACKEND == "local" else "☁️  S3 Key"
    print("\n" + "=" * 65)
    print("  ✅  ETL Pipeline — Run Complete")
    print("=" * 65)
    print(f"  Run ID          : {run_id}")
    print(f"  Status          : SUCCESS")
    print(f"  Duration        : {total_elapsed}s  (extract: {extract_elapsed}s)")
    print(f"  Customers found : {len(customers)}")
    print(f"  Storage backend : {config.STORAGE_BACKEND.upper()}")
    print(f"  {storage_label}  : {data_location}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_pipeline()