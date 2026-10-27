"""
tests/test_normalizer.py — Tests for normalization utility functions.

These functions still exist in src/transformers/normalizer.py
(unchanged from the original week1-and-week2 branch).
"""
from src.transformers.normalizer import (
    normalize_created_timestamp,
    normalize_currency,
    normalize_email,
)


def test_normalize_email_strips_and_lowercases():
    """Email must be trimmed and fully lowercased."""
    assert normalize_email(" Alice@Example.COM ") == "alice@example.com"


def test_normalize_email_none_stays_none():
    """A None email must remain None."""
    assert normalize_email(None) is None


def test_normalize_email_blank_string_returns_none():
    """A blank-only string must become None, not an empty string."""
    assert normalize_email("   ") is None


def test_normalize_currency_strips_and_lowercases():
    """Currency code must be trimmed and lowercased."""
    assert normalize_currency(" USD ") == "usd"


def test_normalize_currency_none_stays_none():
    """A None currency must remain None."""
    assert normalize_currency(None) is None


def test_normalize_created_timestamp_zero():
    """Unix timestamp 0 must equal the Unix epoch in ISO format."""
    result = normalize_created_timestamp(0)
    assert result == "1970-01-01T00:00:00+00:00"


def test_normalize_created_timestamp_positive():
    """A positive Unix timestamp must be converted to a valid ISO string."""
    result = normalize_created_timestamp(1700000000)
    assert result.startswith("2023-")   # 1700000000 is in November 2023
    assert "+00:00" in result            # must be UTC