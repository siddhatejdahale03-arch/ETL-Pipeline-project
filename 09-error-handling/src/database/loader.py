"""
Data loading logic: insert, update, and upsert into the warehouse.
Owner: Rohan (Data Loading & Warehouse Development)
"""
import logging
from src.database.db import SessionLocal
from src.database.models import Transaction

logger = logging.getLogger(__name__)


def insert_records(records: list[dict]) -> int:
    """
    Plain insert, no conflict handling. Useful for a first-run load
    into an empty table, or when you know there are no duplicates.
    """
    if not records:
        return 0

    session = SessionLocal()
    try:
        session.bulk_insert_mappings(Transaction, records)
        session.commit()
        return len(records)
    except Exception:
        session.rollback()
        logger.exception("Insert failed, rolled back")
        raise
    finally:
        session.close()


def create_tables():
    """Run once to create tables based on models.py definitions."""
    from src.database.db import engine, Base
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_tables()
    print("Tables created.")
