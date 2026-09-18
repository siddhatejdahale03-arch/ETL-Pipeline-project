# ETL Pipeline Project

A production-grade **Extract → Transform → Load** pipeline built in Python.

**Week 1 scope:** Stripe Customer extraction → S3 Raw Data Lake

---

## 🏗️ Architecture

```
src/
├── main.py                  # Pipeline orchestrator (entry point)
├── config.py                # Config & secrets loader (fail-fast validation)
├── models/
│   └── customer.py          # Pydantic v2 Customer model (full Stripe schema)
├── extractors/
│   ├── base.py              # Abstract base extractor (Generic[T])
│   └── stripe_extractor.py  # Stripe /v1/customers — full pagination + retry
├── loaders/
│   └── s3_loader.py         # S3 raw data lake (Hive-partitioned paths)
└── utils/
    ├── logger.py            # JSON structured logger
    └── retry.py             # Tenacity retry decorator

tests/
├── test_stripe_extractor.py # Unit tests (mocked HTTP)
└── test_s3_loader.py        # Unit tests (mocked S3)
```

---

## ⚡ Quick Start

### 1. Set up environment

```bash
cd ETL_Pipeline_Project
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure secrets

```bash
cp .env.example .env
# Edit .env with your real Stripe API key and AWS credentials
```

### 3. Run the pipeline

```bash
cd src
python main.py
```

### 4. Run tests

```bash
cd ETL_Pipeline_Project
pip install pytest
pytest tests/ -v
```

---

## 📦 S3 Data Structure

Raw data is written to a Hive-partitioned path:

```
s3://<bucket>/raw/stripe/customers/year=2026/month=09/day=18/<run-id>/data.json
s3://<bucket>/raw/stripe/customers/year=2026/month=09/day=18/<run-id>/_manifest.json
```

This structure is directly queryable by **AWS Athena** and compatible with **AWS Glue** crawlers.

### data.json schema

```json
{
  "run_id": "uuid",
  "source": "stripe",
  "entity": "customers",
  "extracted_at": "2026-09-18T13:45:00+00:00",
  "record_count": 1234,
  "records": [ ... ]
}
```

### _manifest.json schema

```json
{
  "run_id": "uuid",
  "source": "stripe",
  "entity": "customers",
  "extracted_at": "2026-09-18T13:45:00+00:00",
  "record_count": 1234,
  "s3_bucket": "your-bucket",
  "s3_key": "raw/stripe/customers/...",
  "status": "success"
}
```

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `STRIPE_API_KEY` | ✅ | — | Stripe secret key |
| `STRIPE_PAGE_LIMIT` | ❌ | `100` | Records per Stripe page (1–100) |
| `AWS_ACCESS_KEY_ID` | ✅ | — | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | ✅ | — | AWS credentials |
| `AWS_REGION` | ✅ | — | AWS region (e.g. `us-east-1`) |
| `AWS_BUCKET_NAME` | ✅ | — | Target S3 bucket |
| `S3_RAW_PREFIX` | ❌ | `raw` | Top-level S3 prefix |
| `MAX_RETRY_ATTEMPTS` | ❌ | `3` | API call retry attempts |
| `LOG_LEVEL` | ❌ | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

---

## 🗺️ Roadmap

| Week | Milestone |
|---|---|
| **1** ✅ | Stripe extraction → S3 raw data lake |
| **2** | Transform layer — normalise, deduplicate, type-cast |
| **3** | Salesforce integration |
| **4** | Orchestration (Airflow / Lambda), alerting, CI/CD |
