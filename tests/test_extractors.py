"""Tests for the extractors. We use a fake requests.get, so no real API is called."""
import pytest

from src.extractors import base_extractor
from src.extractors.salesforce_extractor import SalesforceExtractor
from src.extractors.stripe_extractor import StripeExtractor
from src.utils.retry import RateLimitError


class FakeResponse:
    def __init__(self, body, status_code=200, headers=None):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self.body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def fake_get_returning(responses, calls):
    """Make a fake requests.get that returns the given responses one by one."""
    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append(dict(params or {}))
        return responses.pop(0)
    return fake_get


def test_stripe_follows_cursor_pagination(monkeypatch):
    calls = []
    responses = [
        FakeResponse({"data": [{"id": "cus_1"}, {"id": "cus_2"}], "has_more": True}),
        FakeResponse({"data": [{"id": "cus_3"}], "has_more": False}),
    ]
    monkeypatch.setattr(base_extractor.requests, "get", fake_get_returning(responses, calls))

    records = StripeExtractor().fetch_all("customers")

    assert [r["id"] for r in records] == ["cus_1", "cus_2", "cus_3"]
    assert "starting_after" not in calls[0]
    assert calls[1]["starting_after"] == "cus_2"  # cursor = last id of page 1


def test_salesforce_follows_next_records_url(monkeypatch):
    calls = []
    responses = [
        FakeResponse({"records": [{"Id": "1"}], "done": False, "nextRecordsUrl": "/next"}),
        FakeResponse({"records": [{"Id": "2"}], "done": True}),
    ]
    monkeypatch.setattr(base_extractor.requests, "get", fake_get_returning(responses, calls))

    records = SalesforceExtractor().run_query("SELECT Id FROM Account")

    assert [r["Id"] for r in records] == ["1", "2"]


def test_rate_limit_is_retried(monkeypatch):
    calls = []
    responses = [
        FakeResponse({}, status_code=429, headers={"Retry-After": "0"}),
        FakeResponse({"data": [{"id": "cus_1"}], "has_more": False}),
    ]
    monkeypatch.setattr(base_extractor.requests, "get", fake_get_returning(responses, calls))
    monkeypatch.setattr(base_extractor.get_json.retry, "sleep", lambda seconds: None)  # don't wait in tests

    records = StripeExtractor().fetch_all("customers")

    assert len(calls) == 2  # first call hit 429, second worked
    assert records == [{"id": "cus_1"}]


def test_rate_limit_gives_up_after_max_attempts(monkeypatch):
    calls = []
    responses = [FakeResponse({}, status_code=429, headers={"Retry-After": "0"}) for _ in range(5)]
    monkeypatch.setattr(base_extractor.requests, "get", fake_get_returning(responses, calls))
    monkeypatch.setattr(base_extractor.get_json.retry, "sleep", lambda seconds: None)

    with pytest.raises(RateLimitError):
        StripeExtractor().fetch_all("customers")


def test_demo_mode_reads_sample_files():
    records = StripeExtractor().extract()
    types = {r["_type"] for r in records}
    assert types == {"customer", "charge"}
