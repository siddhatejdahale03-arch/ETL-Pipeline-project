"""Map cleaned source frames → unified DW schema."""
from datetime import datetime, timezone

import polars as pl

from src.utils.logger import get_logger

log = get_logger("mapper")

UTC = "UTC"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _force_utc(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    """Guarantee every listed column is datetime[us, UTC]."""
    exprs = []
    for col in columns:
        if col not in df.columns:
            continue
        dtype = df.schema[col]
        if dtype == pl.Utf8:
            # String → parse (tolerate "Z", "+00:00", or plain ISO)
            exprs.append(
                pl.col(col)
                .str.replace("Z", "+00:00", literal=True)
                .str.to_datetime(strict=False)
                .dt.replace_time_zone(UTC, strict=False)
                .alias(col)
            )
        elif isinstance(dtype, pl.Datetime):
            if dtype.time_zone is None:
                # Naive → attach UTC
                exprs.append(
                    pl.col(col).dt.replace_time_zone(UTC, strict=False).alias(col)
                )
            else:
                # Aware → convert to UTC
                exprs.append(
                    pl.col(col).dt.convert_time_zone(UTC).alias(col)
                )
        else:
            # Date or other → cast to Datetime then attach UTC
            exprs.append(
                pl.col(col)
                .cast(pl.Datetime("us"))
                .dt.replace_time_zone(UTC, strict=False)
                .alias(col)
            )
    return df.with_columns(exprs) if exprs else df


def to_unified_customers(
    stripe_df: pl.DataFrame, sf_df: pl.DataFrame
) -> pl.DataFrame:
    frames = []
    now = _now_utc()

    if stripe_df is not None and stripe_df.height:
        df = _force_utc(stripe_df, ["created_at"])
        frames.append(
            df.with_columns(
                [
                    pl.lit("stripe").alias("source_system"),
                    pl.lit(None, dtype=pl.Utf8).alias("industry"),
                    pl.lit(None, dtype=pl.Float64).alias("annual_revenue_usd"),
                    pl.col("created_at").alias("updated_at"),
                    pl.lit(now, dtype=pl.Datetime("us", UTC)).alias("ingested_at"),
                ]
            )
        )

    if sf_df is not None and sf_df.height:
        df = _force_utc(sf_df, ["created_at", "updated_at"])
        frames.append(
            df.with_columns(
                [
                    pl.lit("salesforce").alias("source_system"),
                    pl.lit(False).alias("is_delinquent"),
                    pl.lit(None, dtype=pl.Utf8).alias("email"),
                    pl.lit(now, dtype=pl.Datetime("us", UTC)).alias("ingested_at"),
                ]
            )
        )

    if not frames:
        return pl.DataFrame()

    unified = pl.concat(frames, how="diagonal_relaxed").unique(
        subset=["customer_id", "source_system"], keep="last"
    )
    log.info("mapped_unified_customers", rows=unified.height)
    return unified


def to_unified_transactions(
    stripe_df: pl.DataFrame, sf_df: pl.DataFrame
) -> pl.DataFrame:
    frames = []
    now = _now_utc()

    if stripe_df is not None and stripe_df.height:
        df = _force_utc(stripe_df, ["occurred_at"])
        frames.append(
            df.with_columns(
                [
                    pl.lit("stripe").alias("source_system"),
                    pl.lit(now, dtype=pl.Datetime("us", UTC)).alias("ingested_at"),
                ]
            )
        )

    if sf_df is not None and sf_df.height:
        df = _force_utc(sf_df, ["occurred_at"])
        frames.append(
            df.with_columns(
                [
                    pl.lit("salesforce").alias("source_system"),
                    pl.lit(now, dtype=pl.Datetime("us", UTC)).alias("ingested_at"),
                ]
            )
        )

    if not frames:
        return pl.DataFrame()

    unified = pl.concat(frames, how="diagonal_relaxed").unique(
        subset=["transaction_id", "source_system"], keep="last"
    )
    log.info("mapped_unified_transactions", rows=unified.height)
    return unified