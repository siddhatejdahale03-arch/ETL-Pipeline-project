"""
Data loading logic: insert, update, and upsert into the warehouse.
Owner: Rohan (Data Loading & Warehouse Development)
"""
from src.database.db import SessionLocal


def create_tables():
    """Run once to create tables based on models.py definitions."""
    from src.database.db import engine, Base
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
    print("Tables created.")
