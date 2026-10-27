"""
tests/test_validator.py — Tests for the customer record validator.

These functions still exist in src/validators/validator.py
(unchanged from the original week1-and-week2 branch).
"""
import pytest

from src.validators.validator import (
    TransformationValidationError,
    ensure_valid_customer_record,
    validate_customer_record,
)


def test_valid_customer_record_returns_no_errors():
    """A fully valid customer record must produce an empty error list."""
    record = {
        "id": "cus_123",
        "email": "alice@example.com",
        "currency": "usd",
        "created": "2026-01-01T00:00:00+00:00",
    }
    assert validate_customer_record(record) == []


def test_missing_customer_id_is_invalid():
    """A record without an 'id' field must fail validation."""
    errors = validate_customer_record({"email": "alice@example.com"})
    assert "id must be a non-empty string" in errors


def test_empty_customer_id_is_invalid():
    """An empty string 'id' must be treated as missing."""
    errors = validate_customer_record({"id": "   "})
    assert "id must be a non-empty string" in errors


def test_invalid_currency_too_short():
    """A currency code shorter than 3 characters must be rejected."""
    errors = validate_customer_record({"id": "cus_123", "currency": "US"})
    assert "currency must be a 3-character ISO code" in errors


def test_invalid_currency_too_long():
    """A currency code longer than 3 characters must be rejected."""
    errors = validate_customer_record({"id": "cus_123", "currency": "USDD"})
    assert "currency must be a 3-character ISO code" in errors


def test_valid_three_char_currency_passes():
    """A valid 3-character ISO currency code must not produce errors."""
    errors = validate_customer_record({"id": "cus_123", "currency": "usd"})
    assert errors == []


def test_ensure_valid_raises_on_invalid_record():
    """ensure_valid_customer_record() must raise TransformationValidationError."""
    with pytest.raises(TransformationValidationError):
        ensure_valid_customer_record({"email": "alice@example.com"})  # missing id


def test_ensure_valid_does_not_raise_on_valid_record():
    """ensure_valid_customer_record() must not raise for a valid record."""
    ensure_valid_customer_record({"id": "cus_valid"})  # should not raise