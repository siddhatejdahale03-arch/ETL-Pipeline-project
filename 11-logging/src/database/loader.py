"""
Data loading logic: insert, update, and upsert into the warehouse.
Owner: Rohan (Data Loading & Warehouse Development)
"""
import logging
from sqlalchemy.dialects.postgresql import insert as pg_insert
from src.database.db import SessionLocal
from src.database.models import Transaction

logger = logging.getLogger(__name__)


def insert_records(records: list[dict]) -> int:
    """Plain insert, no conflict handling."""
    if not records:
        return 0

    session = SessionLocal()
    try:
        session.bulk_insert_mappings(Transaction, records)
        session.commit()
        logger.info("Inserted %d records", len(records))
        return len(records)
    except Exception:
        session.rollback()
        logger.exception("Insert failed, rolled back")
        raise
    finally:
        session.close()


def load_records(records: list[dict]) -> int:
    """Upsert a batch of transformed records into the warehouse."""
    if not records:
        return 0

    session = SessionLocal()
    try:
        stmt = pg_insert(Transaction).values(records)
        update_cols = {
            col.name: getattr(stmt.excluded, col.name)
            for col in Transaction.__table__.columns
            if col.name != "id"
        }
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_=update_cols,
        )
        session.execute(upsert_stmt)
        session.commit()
        logger.info("Upserted %d records", len(records))
        return len(records)
    except Exception:
        session.rollback()
        logger.exception("Upsert failed, rolled back")
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
