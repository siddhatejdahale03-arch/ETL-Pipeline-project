"""
Database connection setup for the warehouse.
Owner: Rohan (Data Loading & Warehouse Development)
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

logger = logging.getLogger(__name__)

DATABASE_URL: str | None = os.getenv("DATABASE_URL")

engine: Engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_session() -> Session:
    """Yield a DB session; use with a context manager or try/finally."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
