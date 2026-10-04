"""
All project settings live here.

Values are read from the .env file (or real environment variables).
If a value is missing, the default written below is used.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The project folder (one level above this config/ folder)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    # ---- Demo mode ----
    # True  = read fake data from data/sample/ (no API keys needed)
    # False = call the real Stripe and Salesforce APIs
    demo_mode: bool = True

    # ---- Stripe ----
    stripe_api_key: str = ""
    stripe_base_url: str = "https://api.stripe.com/v1"
    stripe_page_limit: int = 100

    # ---- Salesforce ----
    salesforce_access_token: str = ""
    salesforce_instance_url: str = ""
    salesforce_api_version: str = "v59.0"

    # ---- AWS S3 (raw data lake) ----
    use_s3: bool = False  # False = save raw JSON to data/raw/ on your computer
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket: str = "etl-raw-data"

    # ---- Data Warehouse ----
    dw_connection_string: str = "postgresql+psycopg2://etl:etl@localhost:5433/dw"

    # ---- Alerts ----
    slack_webhook_url: str = ""
    alert_email: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""      # your Gmail address
    smtp_password: str = ""  # a Gmail "App Password", NOT your normal password

    # ---- General ----
    max_retry_attempts: int = 3
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Create the settings only once and reuse them everywhere."""
    return Settings()
