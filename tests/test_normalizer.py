from transformers.normalizer import (
    normalize_created_timestamp,
    normalize_currency,
    normalize_email,
)


def test_normalize_email():
    assert normalize_email(" Alice@Example.COM ") == "alice@example.com"


def test_normalize_currency():
    assert normalize_currency(" USD ") == "usd"


def test_normalize_created_timestamp():
    result = normalize_created_timestamp(0)

    assert result == "1970-01-01T00:00:00+00:00"