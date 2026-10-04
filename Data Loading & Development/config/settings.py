"""Centralized configuration loaded from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Stripe
    stripe_api_key: str = "sk_test_dummy"
    stripe_base_url: str = "https://api.stripe.com/v1"

    # Salesforce
    salesforce_client_id: str = ""
    salesforce_client_secret: str = ""
    salesforce_username: str = ""
    salesforce_password: str = ""
    salesforce_security_token: str = ""
    salesforce_base_url: str = ""

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket: str = "etl-raw-data"

    # Data Warehouse
    dw_connection_string: str = "postgresql+psycopg2://user:pass@localhost:5432/dw"

    # Alerts
    slack_webhook_url: str = ""
    alert_email: str = ""

    # App
    log_level: str = "INFO"
    env: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()