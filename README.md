# Enterprise ETL Pipeline & Data Warehouse Synchronizer

Pulls business data from **Stripe** and **Salesforce**, cleans it, converts it
into one shared format, and saves it into a **PostgreSQL data warehouse**.
**Apache Airflow** runs it every day at 02:00 UTC.

📖 **Full documentation:** [docs/PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md)

## How the data flows

```
 Stripe API ─────┐                                   ┌─> customers table
 (customers,     │   EXTRACT        SAVE RAW          │
  charges)       ├─> extractors ──> S3 / data/raw ──> TRANSFORM ──> LOAD ──┤
 Salesforce API ─┘   (pagination,   (backup of the    (clean +     (upsert)└─> transactions table
 (accounts,           rate limits,    original JSON)    unify)
  opportunities)      retries)
```

## Folder map — who owns what

| Folder / file | What it does | Owner |
|---|---|---|
| `config/settings.py` | Reads all settings from `.env` | Sumit |
| `src/models/` | Pydantic models: what each record should look like | Siddhatej |
| `src/extractors/` | Download data from the APIs (pagination, 429 handling, retries) | Siddhatej |
| `src/loaders/s3_loader.py` | Save raw JSON to S3 (or `data/raw/` on your laptop) | Siddhatej |
| `src/transformers/cleaner.py` | Fix dates, currencies, emails, skip bad records | Bhoomi |
| `src/transformers/mapper.py` | Merge both sources into one unified schema | Bhoomi |
| `src/loaders/db_loader.py` + `sql/schema.sql` | Create tables and upsert into PostgreSQL | Rohan |
| `src/pipeline.py` | `run_pipeline()` — runs every step in order | Sumit |
| `dags/etl_dag.py` | Airflow schedule (one task that calls `run_pipeline()`) | Sumit |
| `src/utils/alerts.py` | Slack + email alerts on failure | Sumit |
| `src/utils/logger.py`, `retry.py` | Logging and retry helpers | Sumit |
| `tests/` | Pytest tests | everyone |
| `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml` | Docker + CI | Sumit |

## Run it on your laptop

**Demo mode** (`DEMO_MODE=true`) uses fake data from `data/sample/`, so you
don't need any API keys.

```bash
cp .env.example .env
```

```bash
python3 -m venv .venv && source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

Start the database (Postgres on port 5433):

```bash
docker compose up -d postgres
```

Run the pipeline once:

```bash
python -m src.pipeline
```

Run the tests (database tests are skipped if Postgres is not running):

```bash
pytest
```

## Run with Airflow (in Docker)

Airflow does not install with pip on Python 3.13, so it runs in Docker:

```bash
docker compose up -d airflow
```

Open http://localhost:8080. The login password is printed in the logs
(`docker compose logs airflow | grep -i password`). Turn on the
`etl_synchronizer_daily` DAG.

## Use the real APIs

In `.env` set `DEMO_MODE=false` and fill in `STRIPE_API_KEY`,
`SALESFORCE_ACCESS_TOKEN` and `SALESFORCE_INSTANCE_URL`. To save raw files to S3,
set `USE_S3=true` and fill in the `AWS_*` keys and `S3_BUCKET`.

## Key ideas (for learning)

- **Cursor pagination**: Stripe returns 100 rows at a time; we ask for the next page with `starting_after=<last id>`.
- **Rate limiting**: if an API answers `429 Too Many Requests`, we wait and retry (Tenacity).
- **Incremental load**: the daily run only fetches data from the last 24 hours.
- **Upsert**: new rows are inserted, existing rows (same id + source) are updated, so there are no duplicates.
- **Validation**: Pydantic checks every record; bad ones are logged and skipped instead of crashing the run.

