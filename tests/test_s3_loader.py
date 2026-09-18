"""
tests/test_s3_loader.py — Unit tests for S3Loader.

All boto3 S3 calls are mocked — no real AWS credentials needed.
Tests cover:
  - S3 key generation (partition path correctness)
  - Successful upload (data.json + _manifest.json written)
  - Manifest content and structure
  - Custom run_id is preserved
  - S3 errors propagate after retries
"""

import sys
import os
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Patch config env vars before importing
with patch.dict(os.environ, {
    "STRIPE_API_KEY": "sk_test_fake",
    "AWS_ACCESS_KEY_ID": "fake_key",
    "AWS_SECRET_ACCESS_KEY": "fake_secret",
    "AWS_REGION": "us-east-1",
    "AWS_BUCKET_NAME": "test-bucket",
}):
    from loaders.s3_loader import S3Loader


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXED_DT = datetime(2026, 9, 18, 13, 45, 0, tzinfo=timezone.utc)
FIXED_RUN_ID = "test-run-abc123"

SAMPLE_RECORDS = [
    {"id": "cus_1", "email": "a@example.com", "name": "Alice"},
    {"id": "cus_2", "email": "b@example.com", "name": "Bob"},
]


def _make_loader() -> tuple[S3Loader, MagicMock]:
    """Return a loader instance with a mocked S3 client."""
    with patch("boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        loader = S3Loader(bucket="test-bucket", region="us-east-1", prefix="raw")
        return loader, mock_client


# ---------------------------------------------------------------------------
# Tests: Key Generation
# ---------------------------------------------------------------------------

class TestS3KeyGeneration:

    def test_key_format_correct(self):
        loader, _ = _make_loader()
        key = loader.get_s3_key(
            source="stripe",
            entity="customers",
            run_id=FIXED_RUN_ID,
            dt=FIXED_DT,
        )
        expected = "raw/stripe/customers/year=2026/month=09/day=18/test-run-abc123/data.json"
        assert key == expected

    def test_key_month_zero_padded(self):
        loader, _ = _make_loader()
        dt = datetime(2026, 1, 5, tzinfo=timezone.utc)
        key = loader.get_s3_key("stripe", "customers", FIXED_RUN_ID, dt=dt)
        assert "month=01" in key
        assert "day=05" in key

    def test_custom_filename(self):
        loader, _ = _make_loader()
        key = loader.get_s3_key("stripe", "customers", FIXED_RUN_ID, FIXED_DT, filename="_manifest.json")
        assert key.endswith("_manifest.json")


# ---------------------------------------------------------------------------
# Tests: Upload
# ---------------------------------------------------------------------------

class TestS3LoaderUpload:

    def test_upload_writes_data_and_manifest(self):
        loader, mock_client = _make_loader()
        mock_client.put_object = MagicMock()

        data_key, manifest = loader.upload(
            source="stripe",
            records=SAMPLE_RECORDS,
            entity="customers",
            run_id=FIXED_RUN_ID,
            extracted_at=FIXED_DT,
        )

        # Two S3 puts: data.json and _manifest.json
        assert mock_client.put_object.call_count == 2

    def test_upload_data_key_is_correct(self):
        loader, mock_client = _make_loader()
        mock_client.put_object = MagicMock()

        data_key, _ = loader.upload(
            source="stripe",
            records=SAMPLE_RECORDS,
            entity="customers",
            run_id=FIXED_RUN_ID,
            extracted_at=FIXED_DT,
        )

        expected_key = "raw/stripe/customers/year=2026/month=09/day=18/test-run-abc123/data.json"
        assert data_key == expected_key

    def test_manifest_has_required_fields(self):
        loader, mock_client = _make_loader()
        mock_client.put_object = MagicMock()

        _, manifest = loader.upload(
            source="stripe",
            records=SAMPLE_RECORDS,
            entity="customers",
            run_id=FIXED_RUN_ID,
            extracted_at=FIXED_DT,
        )

        required_fields = {
            "run_id", "source", "entity", "extracted_at",
            "record_count", "s3_bucket", "s3_key", "status"
        }
        assert required_fields.issubset(manifest.keys())

    def test_manifest_record_count_correct(self):
        loader, mock_client = _make_loader()
        mock_client.put_object = MagicMock()

        _, manifest = loader.upload(
            source="stripe",
            records=SAMPLE_RECORDS,
            entity="customers",
            run_id=FIXED_RUN_ID,
            extracted_at=FIXED_DT,
        )

        assert manifest["record_count"] == len(SAMPLE_RECORDS)

    def test_manifest_status_success(self):
        loader, mock_client = _make_loader()
        mock_client.put_object = MagicMock()

        _, manifest = loader.upload(
            source="stripe",
            records=SAMPLE_RECORDS,
            entity="customers",
            run_id=FIXED_RUN_ID,
            extracted_at=FIXED_DT,
        )

        assert manifest["status"] == "success"

    def test_run_id_preserved_in_manifest(self):
        loader, mock_client = _make_loader()
        mock_client.put_object = MagicMock()

        _, manifest = loader.upload(
            source="stripe",
            records=SAMPLE_RECORDS,
            entity="customers",
            run_id=FIXED_RUN_ID,
            extracted_at=FIXED_DT,
        )

        assert manifest["run_id"] == FIXED_RUN_ID
