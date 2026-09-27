"""
Shared test fixtures. Uses an in-memory SQLite DB so tests don't
need a real Postgres instance running.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.db import Base


@pytest.fixture
def test_session():
    """Fresh in-memory SQLite session per test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()
