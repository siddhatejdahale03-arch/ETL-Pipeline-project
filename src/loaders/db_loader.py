"""SQLAlchemy upsert loader for PostgreSQL / Snowflake."""
from typing import Iterable

import polars as pl
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config.settings import get_settings
from src.utils.logger import get_logger

settings = get_settings()
log = get_logger("db_loader")


class DBLoader:
    def __init__(self, connection_string: str | None = None):
        self.engine: Engine = create_engine(
            connection_string or settings.dw_connection_string,
            pool_pre_ping=True,
            future=True,
        )

    def ensure_schema(self, ddl_path: str = "sql/schema.sql") -> None:
        """Execute the DDL file to create tables/indexes if they don't exist."""
        with open(ddl_path, "r", encoding="utf-8") as f:
            ddl = f.read()
        with self.engine.begin() as conn:
            for stmt in [s.strip() for s in ddl.split(";") if s.strip()]:
                conn.execute(text(stmt))
        log.info("schema_ensured")

    def upsert(
        self, table: str, df: pl.DataFrame, conflict_keys: Iterable[str]
    ) -> int:
        """Insert rows, updating existing ones on conflict (PostgreSQL upsert)."""
        if df is None or df.height == 0:
            log.info("upsert_skipped_empty", table=table)
            return 0

        pdf = df.to_pandas()
        # pandas turns missing values into NaN/NaT; the database needs None (NULL)
        pdf = pdf.astype(object).where(pdf.notna(), None)
        cols = list(pdf.columns)
        conflict_keys = list(conflict_keys)
        update_cols = [c for c in cols if c not in conflict_keys]

        placeholders = ", ".join([f":{c}" for c in cols])
        col_list = ", ".join(cols)
        conflict_list = ", ".join(conflict_keys)
        set_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        stmt = text(
            f"""
            INSERT INTO {table} ({col_list})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_list})
            DO UPDATE SET {set_clause}
            """
        )

        rows = pdf.to_dict(orient="records")
        with self.engine.begin() as conn:
            conn.execute(stmt, rows)

        log.info("upsert_ok", table=table, rows=len(rows))
        return len(rows)

    def fetch_count(self, table: str) -> int:
        """Return row count — useful for validation & tests."""
        with self.engine.begin() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        return int(result or 0)