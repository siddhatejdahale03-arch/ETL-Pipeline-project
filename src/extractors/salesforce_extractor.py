"""
Download Accounts and Opportunities from Salesforce using SOQL queries.

Salesforce pagination:
    The first answer contains up to 2000 rows. If there are more, it gives
    a "nextRecordsUrl". We call that URL until "done" is true.
"""
from datetime import datetime

from config.settings import get_settings
from src.extractors.base_extractor import get_json, load_sample
from src.utils.logger import get_logger

log = get_logger("salesforce")

ACCOUNT_QUERY = (
    "SELECT Id, Name, Industry, AnnualRevenue, CreatedDate, LastModifiedDate FROM Account"
)
OPPORTUNITY_QUERY = (
    "SELECT Id, AccountId, Name, Amount, StageName, CloseDate, LastModifiedDate FROM Opportunity"
)


class SalesforceExtractor:
    def __init__(self):
        self.settings = get_settings()
        self.headers = {"Authorization": f"Bearer {self.settings.salesforce_access_token}"}
        self.base_url = self.settings.salesforce_instance_url.rstrip("/")

    def run_query(self, soql: str, since: datetime | None = None) -> list[dict]:
        """Run one SOQL query and follow nextRecordsUrl until all rows are read."""
        if since:  # incremental load: only rows changed after `since`
            soql += f" WHERE LastModifiedDate >= {since.strftime('%Y-%m-%dT%H:%M:%SZ')}"

        url = f"{self.base_url}/services/data/{self.settings.salesforce_api_version}/query"
        body = get_json(url, self.headers, {"q": soql})
        all_records = body["records"]

        while not body.get("done", True):
            next_url = self.base_url + body["nextRecordsUrl"]
            body = get_json(next_url, self.headers)
            all_records.extend(body["records"])

        log.info("query_done", rows=len(all_records))
        return all_records

    def extract(self, since: datetime | None = None) -> list[dict]:
        """Return accounts + opportunities. Each record gets a '_type' tag."""
        if self.settings.demo_mode:
            log.info("demo_mode", detail="reading data/sample/salesforce_*.json")
            accounts = load_sample("salesforce_accounts.json")
            opportunities = load_sample("salesforce_opportunities.json")
        else:
            accounts = self.run_query(ACCOUNT_QUERY, since)
            opportunities = self.run_query(OPPORTUNITY_QUERY, since)

        for record in accounts:
            record["_type"] = "account"
        for record in opportunities:
            record["_type"] = "opportunity"

        log.info("extract_done", accounts=len(accounts), opportunities=len(opportunities))
        return accounts + opportunities
