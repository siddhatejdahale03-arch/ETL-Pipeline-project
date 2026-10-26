"""
Shared test setup.

Tests in DB_TEST_FILES need a running PostgreSQL. If the database is not
reachable, those tests are SKIPPED (not failed), so the other tests still run.
This means you can run pytest locally without Docker and still get results.
"""
import pytest
from sqlalchemy import create_engine, text

from config.settings import get_settings

# These test files make real database calls — skip them if Postgres is down
DB_TEST_FILES = ("test_loaders.py", "test_pipeline.py")


def database_is_up() -> bool:
    """Check if the configured PostgreSQL server is reachable."""
    try:
        engine = create_engine(get_settings().dw_connection_string)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    """Automatically skip DB tests when Postgres is not running."""
    if database_is_up():
        return
    skip = pytest.mark.skip(reason="PostgreSQL is not running (docker compose up -d postgres)")
    for item in items:
        if item.path.name in DB_TEST_FILES:
            item.add_marker(skip)
