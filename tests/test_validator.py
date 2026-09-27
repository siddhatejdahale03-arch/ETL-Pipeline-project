import pytest

from validators.validator import (
    TransformationValidationError,
    ensure_valid_customer_record,
    validate_customer_record,
)


def test_valid_customer_record():
    record = {
        "id": "cus_123",
        "email": "alice@example.com",
        "currency": "usd",
        "created": "2026-01-01T00:00:00+00:00",
    }

    assert validate_customer_record(record) == []


def test_missing_customer_id_is_invalid():
    errors = validate_customer_record(
        {
            "email": "alice@example.com",
        }
    )

    assert "id must be a non-empty string" in errors


def test_invalid_currency_is_rejected():
    errors = validate_customer_record(
        {
            "id": "cus_123",
            "currency": "US",
        }
    )

    assert "currency must be a 3-character ISO code" in errors


def test_invalid_record_raises():
    with pytest.raises(TransformationValidationError):
        ensure_valid_customer_record({})