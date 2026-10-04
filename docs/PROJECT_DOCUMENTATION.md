# Enterprise ETL Pipeline & Data Warehouse Synchronizer — Full Documentation

> **Team:** Sumit Achar (orchestration, alerts, DevOps) · Rohan Divekar (data loading & database) ·
> Siddhatej Dahale (extraction, S3) · Bhoomi (transformation & validation)

---

## 1. What this project does

Companies keep business data in many separate tools: payments in **Stripe**, sales in
**Salesforce**. Analysts used to download that data by hand, which was slow and error-prone.

This project does it **automatically, every day**:

1. **Extract**: download the data from the Stripe and Salesforce APIs.
2. **Save raw**: keep an untouched copy of the original data in a data lake (AWS S3).
3. **Transform**: clean it and convert both sources into **one shared format**.
4. **Load**: save it into a central **PostgreSQL data warehouse** without creating duplicates.
5. **Orchestrate**: **Apache Airflow** runs all of this every day at 02:00 UTC.
6. **Alert**: if something fails, the team gets a **Slack** message and an **email**.

**Result:** one single source of truth for the BI / analytics team, refreshed every 24 hours.

---

## 2. Tech stack

| Area | Tool | Why we use it |
|---|---|---|
| Language | Python 3.11+ | Main language |
| Data processing | **Polars** (+ Pandas) | Fast DataFrames for cleaning data |
| Validation | **Pydantic** | Checks that every record has the right fields and types |
| Settings | **pydantic-settings** + `.env` | Keeps API keys out of the code |
| API calls | **Requests** | HTTP GET calls to Stripe / Salesforce |
| Retries | **Tenacity** | Automatically retries failed API calls |
| Database | **SQLAlchemy** + **PostgreSQL** | Connects to and writes into the warehouse |
| Data lake | **AWS S3** (boto3) | Stores raw JSON backups |
| Orchestration | **Apache Airflow 3** | Runs the pipeline on a daily schedule |
| Alerts | Slack Incoming Webhook + Gmail SMTP | Tells us when something breaks |
| Testing | **Pytest** | Automatic tests |
| Deployment | **Docker**, Docker Compose, GitHub Actions | Same environment everywhere + CI |

---

## 3. File structure

```
enterprise-etl-pipeline/
│
├── config/
│   └── settings.py               # Reads ALL settings from .env (API keys, DB URL, alerts…)
│
├── src/                          # All Python source code
│   ├── pipeline.py               # ★ run_pipeline() — runs every step in order
│   │
│   ├── models/                   # "Shapes" of the data (Pydantic)
│   │   ├── source_models.py      #   What Stripe / Salesforce records look like
│   │   └── unified_models.py     #   Our own unified Customer / Transaction format
│   │
│   ├── extractors/               # E = EXTRACT
│   │   ├── base_extractor.py     #   Shared: safe GET request, rate-limit handling, sample data
│   │   ├── stripe_extractor.py   #   Stripe customers + charges (cursor pagination)
│   │   └── salesforce_extractor.py # Salesforce accounts + opportunities (SOQL + nextRecordsUrl)
│   │
│   ├── transformers/             # T = TRANSFORM
│   │   ├── cleaner.py            #   Validate + clean each source (dates, money, emails)
│   │   └── mapper.py             #   Merge both sources into one unified table
│   │
│   ├── loaders/                  # L = LOAD
│   │   ├── s3_loader.py          #   Save raw JSON to S3 (or data/raw/ locally)
│   │   └── db_loader.py          #   Rohan's DBLoader: create tables + UPSERT into PostgreSQL
│   │
│   └── utils/                    # Helpers used everywhere
│       ├── logger.py             #   Logs to screen + logs/etl.log
│       ├── retry.py              #   Tenacity retry rule (@api_retry)
│       └── alerts.py             #   Slack + email alerts
│
├── dags/
│   └── etl_dag.py                # Airflow DAG: daily at 02:00 UTC, calls run_pipeline()
│
├── sql/
│   ├── schema.sql                # Warehouse tables: customers, transactions (+ indexes)
│   └── init_airflow_db.sql       # Creates Airflow's own database in Docker
│
├── data/
│   ├── sample/                   # Fake API data used in DEMO_MODE (no API keys needed)
│   └── raw/                      # Raw JSON backups when USE_S3=false (git-ignored)
│
├── tests/                        # Pytest tests (21 tests)
│   ├── conftest.py               #   Skips DB tests if PostgreSQL is not running
│   ├── test_extractors.py        #   Pagination, rate limits, retries
│   ├── test_transformers.py      #   Cleaning + unified schema
│   ├── test_loaders.py           #   Upsert logic (Rohan's tests + NULL test)
│   └── test_pipeline.py          #   End-to-end run + "no duplicates" check
│
├── docs/
│   └── PROJECT_DOCUMENTATION.md  # This file
│
├── logs/etl.log                  # Log file (created automatically, git-ignored)
│
├── .env                          # YOUR secrets (git-ignored — never commit!)
├── .env.example                  # Template showing every setting
├── requirements.txt              # Python packages
├── pytest.ini                    # Pytest settings
├── Dockerfile                    # Container image for the pipeline
├── .dockerignore
├── docker-compose.yml            # Postgres + pipeline + Airflow
├── .github/workflows/ci.yml      # GitHub Actions: run tests + build Docker on every push
└── README.md                     # Quick start
```

### Who owns what

| Part | Files | Owner |
|---|---|---|
| Extraction + S3 | `src/extractors/`, `src/models/source_models.py`, `src/loaders/s3_loader.py` | Siddhatej |
| Transformation | `src/transformers/`, `src/models/unified_models.py` | Bhoomi |
| Loading + DB | `src/loaders/db_loader.py`, `sql/schema.sql`, `tests/test_loaders.py` | Rohan |
| Orchestration, alerts, DevOps | `src/pipeline.py`, `dags/`, `src/utils/`, `config/`, Docker, CI | Sumit |

---

## 4. Workflow (how data moves)

### 4.1 Big picture

```
                    ┌──────────────────────────────────────────┐
                    │  Apache Airflow  (every day 02:00 UTC)   │
                    │  dags/etl_dag.py → run_pipeline()        │
                    └────────────────────┬─────────────────────┘
                                         │
        ┌────────────────────────────────▼───────────────────────────────┐
        │                        src/pipeline.py                         │
        │                                                                │
        │  1. EXTRACT                                                    │
        │     Stripe API ──► customers, charges                          │
        │     Salesforce API ──► accounts, opportunities                 │
        │                │                                               │
        │  2. SAVE RAW   ▼                                               │
        │     S3: raw/stripe/2026/10/04/020000.json  (or data/raw/)      │
        │                │                                               │
        │  3. TRANSFORM  ▼                                               │
        │     cleaner.py  → validate + clean each source                 │
        │     mapper.py   → unified customers + unified transactions     │
        │                │                                               │
        │  4. LOAD       ▼                                               │
        │     DBLoader.ensure_schema()  → create tables if missing       │
        │     DBLoader.upsert(...)      → insert new / update existing   │
        └────────────────────────────────┬───────────────────────────────┘
                                         │
                       ┌─────────────────▼──────────────────┐
                       │   PostgreSQL Data Warehouse        │
                       │   • customers   • transactions     │
                       └─────────────────┬──────────────────┘
                                         ▼
                              BI / Analytics dashboards

   If anything fails → Airflow retries 2× (5 min apart) → Slack + Email alert
```

### 4.2 Step by step

**Step 0 — Start.** Airflow triggers `run_pipeline(incremental=True)` at 02:00 UTC.
You can also run it by hand: `python -m src.pipeline` (full reload).

**Step 1 — Extract** (`src/extractors/`)
- **Incremental load:** the daily run only asks for records from the **last 24 hours**
  (Stripe: `created[gte]=…`, Salesforce: `WHERE LastModifiedDate >= …`).
- **Stripe cursor pagination:** ask for 100 records → if `has_more` is true, ask again with
  `starting_after=<id of the last record>` → repeat until done.
- **Salesforce pagination:** run a SOQL query → follow `nextRecordsUrl` until `done` is true.
- **Rate limits:** if the API answers **429 Too Many Requests**, wait for the `Retry-After`
  seconds and try again.
- **Network errors:** Tenacity retries up to 3 times (waiting 2s, 4s, 8s…).
- Every record gets a `_type` tag (`customer`, `charge`, `account`, `opportunity`).
- **DEMO_MODE=true:** instead of calling APIs, the extractors read files from `data/sample/`.

**Step 2 — Save raw data** (`src/loaders/s3_loader.py`)
- The original JSON is saved **before** any changes, so we can always re-process it later.
- `USE_S3=true` → `s3://<bucket>/raw/<source>/YYYY/MM/DD/HHMMSS.json`
- `USE_S3=false` → same path inside `data/raw/` on your computer.

**Step 3a — Clean** (`src/transformers/cleaner.py`)

| Problem in raw data | What we do |
|---|---|
| Record is missing a required field | Pydantic rejects it → logged as `bad_record_skipped`, pipeline continues |
| Stripe dates are Unix numbers (`1759363200`) | Convert to UTC datetime |
| Salesforce dates have time zones (`+0530`) | Convert to UTC |
| Stripe amounts are in **cents** (`4999`) | Divide by 100 → `49.99` |
| Different currencies (EUR, GBP, INR) | Convert to **USD** |
| Emails like `"  Alice@Example.COM "` | Trim + lowercase → `alice@example.com` |
| Empty text `""` | Becomes `NULL` |
| Status like `"SUCCEEDED"` | Lowercase → `succeeded` |

**Step 3b — Map to unified schema** (`src/transformers/mapper.py`)

| Unified table | From Stripe | From Salesforce |
|---|---|---|
| `customers` | customers | accounts |
| `transactions` | charges | opportunities |

Every row gets `source_system` (`stripe` / `salesforce`) and `ingested_at` (when we loaded it).
Missing columns are filled with `NULL`, and duplicates are removed.

**Step 4 — Load** (`src/loaders/db_loader.py`)
- `ensure_schema()` runs `sql/schema.sql` (creates tables only if they don't exist).
- `upsert()` uses PostgreSQL `INSERT … ON CONFLICT … DO UPDATE`:
  - new `(id, source_system)` → **insert**
  - existing `(id, source_system)` → **update**
  - so running the pipeline twice **never creates duplicates**.

**Step 5 — Alerts** (`src/utils/alerts.py`)

| Event | Slack | Email |
|---|---|---|
| Full reload finished (`python -m src.pipeline`) | ✅ summary message | — |
| Airflow task failed after 2 retries | ✅ | ✅ |

If `SLACK_WEBHOOK_URL` is empty, Slack is skipped silently.

---

## 5. Data warehouse schema

### `customers`
| Column | Type | Meaning |
|---|---|---|
| `customer_id` | VARCHAR(64) | ID from the source system (PK part 1) |
| `source_system` | VARCHAR(32) | `stripe` or `salesforce` (PK part 2) |
| `email` | VARCHAR(255) | Lowercased email |
| `full_name` | VARCHAR(255) | Person / company name |
| `industry` | VARCHAR(128) | Salesforce only |
| `annual_revenue_usd` | NUMERIC(18,2) | Salesforce only |
| `is_delinquent` | BOOLEAN | Stripe: customer has unpaid invoices |
| `created_at`, `updated_at` | TIMESTAMPTZ | UTC times |
| `ingested_at` | TIMESTAMPTZ | When the pipeline loaded this row |

### `transactions`
| Column | Type | Meaning |
|---|---|---|
| `transaction_id` | VARCHAR(64) | Charge ID / Opportunity ID (PK part 1) |
| `source_system` | VARCHAR(32) | PK part 2 |
| `customer_id` | VARCHAR(64) | Who it belongs to |
| `amount_usd` | NUMERIC(18,2) | Always in USD |
| `status` | VARCHAR(64) | `succeeded`, `failed`, `closed won`… |
| `description` | TEXT | Charge description / opportunity name |
| `occurred_at` | TIMESTAMPTZ | When it happened (UTC) |
| `ingested_at` | TIMESTAMPTZ | When we loaded it |

Example analytics query:
```sql
SELECT source_system, status, COUNT(*), SUM(amount_usd)
FROM transactions
GROUP BY source_system, status
ORDER BY source_system;
```

---

## 6. Configuration (`.env`)

Copy the template first: `cp .env.example .env`

| Setting | Example | Purpose |
|---|---|---|
| `DEMO_MODE` | `true` | `true` = sample data, `false` = real APIs |
| `STRIPE_API_KEY` | `sk_test_…` | Stripe secret key |
| `STRIPE_PAGE_LIMIT` | `100` | Records per Stripe page |
| `SALESFORCE_ACCESS_TOKEN` | — | Salesforce OAuth token |
| `SALESFORCE_INSTANCE_URL` | `https://x.my.salesforce.com` | Your Salesforce domain |
| `USE_S3` | `false` | `true` = upload raw data to S3 |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET` | — | S3 access |
| `DW_CONNECTION_STRING` | `postgresql+psycopg2://etl:etl@localhost:5433/dw` | Warehouse database |
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/services/…` | Optional Slack alerts |
| `ALERT_EMAIL` | `you@gmail.com` | Who receives alert emails |
| `SMTP_HOST`, `SMTP_PORT` | `smtp.gmail.com`, `587` | Mail server |
| `SMTP_USER`, `SMTP_PASSWORD` | Gmail + **App Password** | Account that sends alerts |
| `MAX_RETRY_ATTEMPTS` | `3` | API retry count |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

> 🔒 Never commit `.env`. It is listed in `.gitignore`.

---

## 7. How to run

### 7.1 First-time setup
```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 7.2 Start the database
```bash
docker compose up -d postgres
```

### 7.3 Run the pipeline once
```bash
python -m src.pipeline
```
Expected last line:
```
{'stripe_raw': 7, 'salesforce_raw': 4, 'customers_loaded': 5, 'transactions_loaded': 5}
```
(Demo data has 4 Stripe customers — 1 is broken on purpose and gets skipped.)

### 7.4 Look at the data
```bash
docker compose exec postgres psql -U etl -d dw -c "SELECT * FROM customers;"
```

### 7.5 Run the tests
```bash
pytest
```
21 tests. If PostgreSQL is not running, the 9 database tests are **skipped**, not failed.

### 7.6 Run with Airflow
```bash
docker compose up -d airflow
docker compose logs airflow | grep -i password
```
Open http://localhost:8080 → log in as `admin` with the printed password →
turn on **etl_synchronizer_daily** → click ▶ to trigger a run now.

### 7.7 Run the pipeline in Docker (no local Python)
```bash
docker compose run --rm etl
```

### 7.8 Switch to real APIs
In `.env`: `DEMO_MODE=false` and fill in the Stripe / Salesforce keys.
For S3: `USE_S3=true` + AWS keys.

---

## 8. Testing

| Test file | What it checks |
|---|---|
| `test_extractors.py` | Stripe cursor pagination, Salesforce `nextRecordsUrl`, 429 retry, giving up after max retries, demo mode |
| `test_transformers.py` | Email cleaning, bad records skipped, cents→dollars, currency conversion, UTC dates, unified columns, duplicate removal |
| `test_loaders.py` | Insert, update, empty input, many rows, transactions, schema can run twice, missing values saved as `NULL` |
| `test_pipeline.py` | Full end-to-end run, and running twice creates **no duplicates** |

APIs are never really called in tests — we replace `requests.get` with a fake one.

---

## 9. CI/CD (`.github/workflows/ci.yml`)

On every **push** and **pull request**, GitHub Actions:
1. Starts a PostgreSQL service.
2. Installs `requirements.txt` on Python 3.11.
3. Runs `pytest` (all 21 tests).
4. Builds the Docker image to make sure the `Dockerfile` works.

---

## 10. Logs & troubleshooting

Logs are printed to the screen **and** saved in `logs/etl.log`:
```
2026-10-04 22:02:42 | INFO | pipeline | pipeline_complete | stripe_raw=7 salesforce_raw=4 ...
```

| You see | Meaning / fix |
|---|---|
| `bad_record_skipped` | A source record was invalid — normal, it was skipped |
| `rate_limited` | API said "slow down" — pipeline waits and retries automatically |
| `connection refused … 5433` | Database not running → `docker compose up -d postgres` |
| `email_skipped` | `ALERT_EMAIL` is empty |
| `email_alert_failed … Username and Password not accepted` | Use a Gmail **App Password**, and turn on 2-Step Verification |
| `slack_alert_failed` | Wrong or removed webhook URL |
| `9 skipped` in pytest | PostgreSQL not running — DB tests skipped |
| Airflow can't install with pip | Expected on Python 3.13 — use `docker compose up -d airflow` |

---

## 11. Project timeline (what was delivered)

| Week | Plan | Where it is |
|---|---|---|
| 1 | Pydantic models, `.env` keys, Stripe + Salesforce extraction, cursor pagination, rate limits, raw JSON to S3 | `src/models/`, `config/`, `src/extractors/`, `src/loaders/s3_loader.py` |
| 2 | Clean data with Polars, nulls, dates, currencies, unified schema, Pytest | `src/transformers/`, `tests/test_transformers.py` |
| 3 | SQLAlchemy connection, upsert, end-to-end test | `src/loaders/db_loader.py`, `sql/schema.sql`, `tests/test_loaders.py`, `tests/test_pipeline.py` |
| 4 | Airflow DAG, Slack/Email alerts, Docker, CI/CD | `dags/`, `src/utils/alerts.py`, `Dockerfile`, `docker-compose.yml`, `.github/workflows/` |

---

## 12. Glossary

- **ETL** — Extract, Transform, Load.
- **API** — A web address a program calls to get data.
- **Pagination** — Getting data page by page instead of all at once.
- **Cursor** — A bookmark ("start after this ID") for the next page.
- **Rate limit** — The maximum number of requests an API allows; going over it gives HTTP 429.
- **Incremental load** — Only fetch what changed recently instead of everything.
- **Upsert** — UPDATE if the row exists, INSERT if it doesn't.
- **Data lake (S3)** — Cheap storage for raw files.
- **Data warehouse** — A clean, structured database for analytics.
- **DAG** — Directed Acyclic Graph: Airflow's name for a scheduled workflow.
- **Webhook** — A secret URL you POST a message to (used for Slack).
