"""
tests/test_s3_loader.py — Tests for S3Loader / local file storage.

Updated for the new S3Loader that:
  - reads all settings from config/settings.py (not constructor args)
  - USE_S3=false (default) saves to local data/raw/ folder
  - USE_S3=true uploads to AWS S3
  - write_json(source, records) is the main method
"""
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.loaders.s3_loader import S3Loader


class TestS3LoaderLocalMode:
    """Tests for USE_S3=false (default) — saves to local data/raw/ folder."""

    def test_write_json_creates_file_on_disk(self, tmp_path):
        """write_json() must create a JSON file at the expected path."""
        with patch("src.loaders.s3_loader.PROJECT_ROOT", tmp_path):
            loader = S3Loader()
            loader.settings.use_s3 = False  # local mode
            location = loader.write_json("stripe", [{"id": "cus_1"}])

        assert Path(location).exists()

    def test_write_json_file_contains_valid_json(self, tmp_path):
        """The saved file must contain valid JSON with the correct records."""
        records = [{"id": "cus_1", "email": "a@b.com"}]
        with patch("src.loaders.s3_loader.PROJECT_ROOT", tmp_path):
            loader = S3Loader()
            loader.settings.use_s3 = False
            location = loader.write_json("stripe", records)

        saved = json.loads(Path(location).read_text())
        assert saved == records

    def test_write_json_returns_file_path_string(self, tmp_path):
        """write_json() must return a non-empty string path."""
        with patch("src.loaders.s3_loader.PROJECT_ROOT", tmp_path):
            loader = S3Loader()
            loader.settings.use_s3 = False
            result = loader.write_json("salesforce", [])

        assert isinstance(result, str)
        assert len(result) > 0

    def test_write_json_path_includes_source_name(self, tmp_path):
        """The path must contain the source name for easy identification."""
        with patch("src.loaders.s3_loader.PROJECT_ROOT", tmp_path):
            loader = S3Loader()
            loader.settings.use_s3 = False
            location = loader.write_json("stripe", [{"id": "1"}])

        assert "stripe" in location

    def test_write_json_empty_records_still_creates_file(self, tmp_path):
        """Even an empty records list must produce a valid JSON file."""
        with patch("src.loaders.s3_loader.PROJECT_ROOT", tmp_path):
            loader = S3Loader()
            loader.settings.use_s3 = False
            location = loader.write_json("stripe", [])

        saved = json.loads(Path(location).read_text())
        assert saved == []


class TestS3LoaderS3Mode:
    """Tests for USE_S3=true — uploads to AWS S3."""

    def test_write_json_calls_put_object(self):
        """In S3 mode, write_json() must call boto3 put_object exactly once."""
        mock_client = MagicMock()
        with patch("boto3.client", return_value=mock_client):
            loader = S3Loader()
            loader.client = mock_client        # inject mock
            loader.settings.use_s3 = True
            loader.write_json("stripe", [{"id": "cus_1"}])

        mock_client.put_object.assert_called_once()

    def test_write_json_s3_returns_s3_uri(self):
        """In S3 mode, the returned location must be an s3:// URI."""
        mock_client = MagicMock()
        with patch("boto3.client", return_value=mock_client):
            loader = S3Loader()
            loader.client = mock_client
            loader.settings.use_s3 = True
            location = loader.write_json("stripe", [{"id": "cus_1"}])

        assert location.startswith("s3://")
