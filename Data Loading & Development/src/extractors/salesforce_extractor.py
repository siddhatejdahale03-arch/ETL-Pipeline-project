"""Salesforce extractor using SOQL + query pagination."""
from typing import Any, Dict, Generator

import requests

from config.settings import get_settings
from src.extractors.base_extractor import BaseExtractor
from src.utils.logger import get_logger

settings = get_settings()
log = get_logger("salesforce_extractor")


class SalesforceExtractor(BaseExtractor):
    name = "salesforce"

    def __init__(self):
        super().__init__(
            base_url=settings.salesforce_base_url,
            headers={"Content-Type": "application/json"},
        )
        self._access_token: str | None = None
        self._instance_url: str | None = None

    def _authenticate(self) -> None:
        if self._access_token:
            return
        payload = {
            "grant_type": "password",
            "client_id": settings.salesforce_client_id,
            "client_secret": settings.salesforce_client_secret,
            "username": settings.salesforce_username,
            "password": settings.salesforce_password
            + settings.salesforce_security_token,
        }
        resp = requests.post(
            f"{settings.salesforce_base_url}/services/oauth2/token",
            data=payload,
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        self._access_token = body["access_token"]
        self._instance_url = body["instance_url"]
        self.session.headers.update(
            {"Authorization": f"Bearer {self._access_token}"}
        )
        log.info("salesforce_authenticated")

    def _soql(self, query: str) -> Generator[Dict[str, Any], None, None]:
        self._authenticate()
        url = f"{self._instance_url}/services/data/v59.0/query"
        params = {"q": query}
        while url:
            payload = self._get(url, params=params)
            for record in payload.get("records", []):
                record.pop("attributes", None)
                yield record
            next_url = payload.get("nextRecordsUrl")
            if next_url:
                url = f"{self._instance_url}{next_url}"
                params = None
            else:
                url = None

    def extract(
        self, since: str | None = None
    ) -> Generator[Dict[str, Any], None, None]:
        log.info("salesforce_extract_start", since=since)

        acct_where = f" WHERE LastModifiedDate >= {since}" if since else ""
        acct_query = (
            "SELECT Id, Name, Industry, AnnualRevenue, CreatedDate, LastModifiedDate "
            f"FROM Account{acct_where}"
        )
        for acc in self._soql(acct_query):
            yield {"_type": "account", **acc}

        opp_where = f" WHERE LastModifiedDate >= {since}" if since else ""
        opp_query = (
            "SELECT Id, AccountId, Name, Amount, StageName, CloseDate "
            f"FROM Opportunity{opp_where}"
        )
        for opp in self._soql(opp_query):
            yield {"_type": "opportunity", **opp}