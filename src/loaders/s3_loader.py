"""
Save the RAW API data (before any cleaning) to the data lake.

    USE_S3=true   -> upload to AWS S3:  s3://<bucket>/raw/stripe/2026/10/04/020000.json
    USE_S3=false  -> save on your computer: data/raw/stripe/2026/10/04/020000.json

Keeping raw data means we can re-run transforms later without calling the APIs again.
"""
import json
from datetime import datetime, timezone

from config.settings import PROJECT_ROOT, get_settings
from src.utils.logger import get_logger

log = get_logger("s3_loader")


class S3Loader:
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        if self.settings.use_s3:
            import boto3  # only needed when S3 is switched on

            self.client = boto3.client(
                "s3",
                region_name=self.settings.aws_region,
                aws_access_key_id=self.settings.aws_access_key_id or None,
                aws_secret_access_key=self.settings.aws_secret_access_key or None,
            )

    def write_json(self, source: str, records: list[dict]) -> str:
        """Save records and return where they were saved."""
        timestamp = datetime.now(timezone.utc).strftime("%Y/%m/%d/%H%M%S")
        key = f"raw/{source}/{timestamp}.json"
        body = json.dumps(records, default=str, indent=2)

        if self.client:
            self.client.put_object(Bucket=self.settings.s3_bucket, Key=key,
                                   Body=body.encode("utf-8"), ContentType="application/json")
            location = f"s3://{self.settings.s3_bucket}/{key}"
        else:
            path = PROJECT_ROOT / "data" / key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
            location = str(path)

        log.info("raw_saved", source=source, rows=len(records), location=location)
        return location
