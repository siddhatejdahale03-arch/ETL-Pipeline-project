"""End-to-end test: run the whole pipeline in demo mode against PostgreSQL."""
from src.pipeline import run_pipeline


def test_pipeline_end_to_end_in_demo_mode():
    first = run_pipeline(incremental=False)
    assert first["customers_loaded"] == 5      # 3 valid Stripe + 2 Salesforce
    assert first["transactions_loaded"] == 5   # 3 Stripe + 2 Salesforce

    # Running again must NOT create duplicates (upsert)
    from src.loaders.db_loader import DBLoader
    run_pipeline(incremental=False)
    loader = DBLoader()
    assert loader.fetch_count("customers") >= 5
    with loader.engine.connect() as conn:
        from sqlalchemy import text
        dupes = conn.execute(text(
            "SELECT COUNT(*) FROM (SELECT customer_id, source_system FROM customers "
            "GROUP BY 1, 2 HAVING COUNT(*) > 1) d"
        )).scalar()
    assert dupes == 0
