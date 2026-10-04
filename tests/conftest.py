"""
Shared test setup.

Tests in DB_TEST_FILES need a running PostgreSQL. If the database is not
reachable, those tests are SKIPPED (not failed), so the other tests still run.
"""
import pytest
from sqlalchemy import create_engine, text

from config.settings import get_settings

DB_TEST_FILES = ("test_loaders.py", "test_pipeline.py")


def database_is_up() -> bool:
    try:
        engine = create_engine(get_settings().dw_connection_string)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    if database_is_up():
        return
    skip = pytest.mark.skip(reason="PostgreSQL is not running (docker compose up -d postgres)")
    for item in items:
        if item.path.name in DB_TEST_FILES:
            item.add_marker(skip)
