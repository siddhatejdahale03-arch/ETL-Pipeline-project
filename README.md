# 🚀 ETL Pipeline Project

> **Automated data pipeline** that extracts customer data from Stripe, cleans it, and stores it in a structured raw data lake — ready for analytics, dashboards, and CRM sync.

---

## 📋 Table of Contents

- [What This Project Does](#what-this-project-does)
- [Project Structure](#project-structure)
- [Team Onboarding — Start Here](#team-onboarding--start-here)
- [Environment Variables — Full Setup Guide](#environment-variables--full-setup-guide)
- [Running the Pipeline](#running-the-pipeline)
- [Running Tests](#running-tests)
- [Seeding Test Data](#seeding-test-data)
- [Storage Backends](#storage-backends)
- [Data Output Format](#data-output-format)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)

---

## What This Project Does

This is an **ETL (Extract → Transform → Load)** pipeline:

```
🏦 Stripe API          →       📥 Extract        →       💾 Store (Local or S3)
(Customer records)          (All pages, retried)        (Partitioned by date)
```

**Week 1 (current):** Pull all customers from Stripe → save raw JSON to local disk or AWS S3 in a Hive-partitioned structure queryable by Athena/Glue.

**Upcoming weeks:** Transform layer → Salesforce sync → Airflow scheduling → Monitoring.

---

## Project Structure

```
ETL_Pipeline_Project/
│
├── .env                        ← YOUR SECRETS (never commit this)
├── .env.example                ← Template — copy this to .env and fill in
├── .gitignore
├── README.md
├── requirements.txt
│
├── scripts/
│   └── seed_stripe_test_data.py   ← Creates 10 fake customers in Stripe test mode
│
├── src/
│   ├── main.py                    ← Pipeline entry point (run this)
│   ├── config.py                  ← Loads & validates all env vars
│   │
│   ├── extractors/
│   │   ├── base.py                ← Abstract base class for all extractors
│   │   └── stripe_extractor.py    ← Stripe /v1/customers (full pagination + retry)
│   │
│   ├── loaders/
│   │   ├── local_loader.py        ← Save to local disk (free, no cloud needed)
│   │   └── s3_loader.py           ← Save to AWS S3 (production)
│   │
│   ├── models/
│   │   └── customer.py            ← Pydantic v2 Customer data model
│   │
│   └── utils/
│       ├── logger.py              ← JSON structured logger
│       └── retry.py               ← Retry logic (handles rate limits, timeouts)
│
└── tests/
    ├── test_stripe_extractor.py   ← 9 unit tests (mocked HTTP)
    └── test_s3_loader.py          ← 7 unit tests (mocked S3)
```

---

## Team Onboarding — Start Here

> **Every team member must follow these steps before running anything.**

### Step 1 — Clone the repo

```bash
git clone https://github.com/siddhatejdahale03-arch/ETL-Pipeline-project.git
cd ETL-Pipeline-project
git checkout siddhatej-dahale
```

### Step 2 — Create and activate virtual environment

```bash
python3 -m venv venv

# Mac / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Set up your `.env` file

```bash
cp .env.example .env
```

Then **open `.env` and fill in your credentials** — see the full guide below 👇

### Step 5 — Run the pipeline

```bash
cd src
python main.py
```

---

## Environment Variables — Full Setup Guide

> ⚠️ **IMPORTANT:** Never commit your `.env` file. It is in `.gitignore`. Each team member has their own credentials.

Open `.env` and fill in each section:

---

### 🔵 Section 1 — Stripe (REQUIRED)

```env
STRIPE_API_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_PAGE_LIMIT=100
```

#### How to get your Stripe API Key:

1. Go to → **https://dashboard.stripe.com/apikeys**
2. Log in with the **shared team Stripe account** (ask team lead for login)
3. Under **"Standard keys"** → copy the **Secret key**
   - Test mode key starts with: `sk_test_...`
   - Live mode key starts with: `sk_live_...`
4. Paste it as `STRIPE_API_KEY`

> ✅ Use `sk_test_...` during development — it costs nothing and is completely safe.
> ⛔ Only use `sk_live_...` on the production server — never on your local machine.

| Variable | Required | Default | Description |
|---|---|---|---|
| `STRIPE_API_KEY` | ✅ Yes | — | Stripe secret key |
| `STRIPE_PAGE_LIMIT` | ❌ No | `100` | Records per API page (max 100) |

---

### 🟠 Section 2 — Storage Backend (REQUIRED — choose one)

```env
STORAGE_BACKEND=local
```

| Value | When to use |
|---|---|
| `local` | Development on your machine (free, no cloud needed) |
| `s3` | Staging / Production (requires AWS credentials below) |

> 👉 **For development, set `STORAGE_BACKEND=local`** and skip the AWS section entirely.

---

### 🟡 Section 3 — Local Storage (only needed when `STORAGE_BACKEND=local`)

```env
LOCAL_STORAGE_PATH=./data/raw
```

Data will be saved to this path on your machine:
```
./data/raw/stripe/customers/year=2026/month=09/day=18/<run-id>/data.json
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `LOCAL_STORAGE_PATH` | ❌ No | `./data/raw` | Where to save data files locally |

---

### 🔴 Section 4 — AWS S3 (only needed when `STORAGE_BACKEND=s3`)

```env
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1
AWS_BUCKET_NAME=your-etl-raw-bucket
S3_RAW_PREFIX=raw
```

#### How to get AWS credentials:

> Ask the **team lead / AWS admin** to create an IAM user for you. They should follow these steps:

**Team Lead Instructions (do this once per team member):**

1. Go to → **https://console.aws.amazon.com/iam/home#/users**
2. Click **"Create user"** → name: `etl-{firstname}` (e.g. `etl-siddhatej`)
3. Click **"Attach policies directly"** → select **`AmazonS3FullAccess`**
4. Click **"Create user"** → open the user → **"Security credentials"** tab
5. Click **"Create access key"** → select **"Application running outside AWS"**
6. Share the **Access Key ID** and **Secret Access Key** with the team member securely

**Team Member:**
- Paste the Access Key ID as `AWS_ACCESS_KEY_ID`
- Paste the Secret Access Key as `AWS_SECRET_ACCESS_KEY`
- Set `AWS_REGION` to the region the S3 bucket is in (ask team lead)
- Set `AWS_BUCKET_NAME` to the shared team bucket name (ask team lead)

| Variable | Required for S3 | Description |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | ✅ Yes | Your personal IAM access key |
| `AWS_SECRET_ACCESS_KEY` | ✅ Yes | Your personal IAM secret key |
| `AWS_REGION` | ✅ Yes | AWS region (e.g. `us-east-1`, `ap-south-1`) |
| `AWS_BUCKET_NAME` | ✅ Yes | S3 bucket name (shared, ask team lead) |
| `S3_RAW_PREFIX` | ❌ No | Top-level S3 folder prefix (default: `raw`) |

---

### 🟣 Section 5 — Salesforce (OPTIONAL — Week 2+)

```env
SALESFORCE_ACCESS_TOKEN=
SALESFORCE_INSTANCE_URL=
```

Leave these **blank for now**. They will be needed in Week 2 when we build the Salesforce sync. The team lead will share the token when that work begins.

---

### ⚙️ Section 6 — Pipeline Behaviour (OPTIONAL)

```env
MAX_RETRY_ATTEMPTS=3
LOG_LEVEL=INFO
```

| Variable | Default | Options | Description |
|---|---|---|---|
| `MAX_RETRY_ATTEMPTS` | `3` | Any number | How many times to retry failed API calls |
| `LOG_LEVEL` | `INFO` | `DEBUG` `INFO` `WARNING` `ERROR` | Log verbosity |

> 💡 Set `LOG_LEVEL=DEBUG` if you're debugging — it shows every API call in detail.

---

### ✅ Your final `.env` should look like this (local dev):

```env
# ── Stripe ──────────────────────────────────────────────
STRIPE_API_KEY=sk_test_51xxxxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_PAGE_LIMIT=100

# ── Storage ─────────────────────────────────────────────
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./data/raw

# ── AWS (leave blank for local dev) ─────────────────────
AWS_ACCESS_KEY_ID=placeholder
AWS_SECRET_ACCESS_KEY=placeholder
AWS_REGION=us-east-1
AWS_BUCKET_NAME=local

# ── Salesforce (Week 2+, leave blank) ───────────────────
SALESFORCE_ACCESS_TOKEN=
SALESFORCE_INSTANCE_URL=

# ── Pipeline Behaviour ───────────────────────────────────
MAX_RETRY_ATTEMPTS=3
LOG_LEVEL=INFO
```

---

## Running the Pipeline

```bash
# Make sure venv is active
source venv/bin/activate

# Run from project root
python src/main.py
```

**Expected output:**
```
═══════════════════════════════════════════════════════════════════
  ✅  ETL Pipeline — Run Complete
═══════════════════════════════════════════════════════════════════
  Run ID          : 38f6a6dc-6209-4298-961f-5b0b5b2df06f
  Status          : SUCCESS
  Duration        : 1.2s
  Customers found : 10
  Storage backend : LOCAL
  📁 Local Path   : ./data/raw/stripe/customers/year=2026/.../data.json
═══════════════════════════════════════════════════════════════════
```

---

## Running Tests

```bash
# All tests (no credentials needed — everything is mocked)
python -m pytest tests/ -v

# Expected: 16 passed
```

> ✅ Tests use mocked HTTP and mocked S3 — you don't need real Stripe or AWS credentials to run tests.

---

## Seeding Test Data

If your Stripe test account has no customers, run this first:

```bash
python scripts/seed_stripe_test_data.py
```

This creates **10 realistic fake customers** in your Stripe test account. Safe — no real charges, test mode only. Idempotent — won't create duplicates if run multiple times.

---

## Storage Backends

### Local (default — for development)

Data is saved to your machine:
```
data/raw/stripe/customers/
└── year=2026/month=09/day=18/
    └── <run-id>/
        ├── data.json         ← all customer records
        └── _manifest.json    ← run metadata (count, timestamp, status)
```

Switch by setting in `.env`:
```env
STORAGE_BACKEND=local
```

### AWS S3 (for staging / production)

Same folder structure, but in the cloud:
```
s3://your-bucket/raw/stripe/customers/year=2026/month=09/day=18/<run-id>/data.json
```

Switch by setting in `.env`:
```env
STORAGE_BACKEND=s3
```

> No code changes needed — the pipeline auto-detects which loader to use.

---

## Data Output Format

### `data.json`
```json
{
  "run_id": "38f6a6dc-6209-4298-961f-5b0b5b2df06f",
  "source": "stripe",
  "entity": "customers",
  "extracted_at": "2026-09-18T14:16:07+00:00",
  "record_count": 10,
  "records": [
    {
      "id": "cus_VHbnlEevhUC4Jx",
      "name": "Alice Johnson",
      "email": "alice.johnson@example.com",
      "phone": "+14155551234",
      "balance": 0,
      "currency": "usd",
      "created": 1726668987,
      "livemode": false,
      "metadata": { "plan": "premium", "source": "organic" }
    }
  ]
}
```

### `_manifest.json`
```json
{
  "run_id": "38f6a6dc-6209-4298-961f-5b0b5b2df06f",
  "source": "stripe",
  "entity": "customers",
  "extracted_at": "2026-09-18T14:16:07+00:00",
  "record_count": 10,
  "storage": "local",
  "data_path": "./data/raw/stripe/customers/year=2026/month=09/day=18/.../data.json",
  "status": "success"
}
```

---

## Roadmap

| Week | Status | Milestone |
|---|---|---|
| **1** | ✅ Done | Stripe extraction → Raw data lake (local + S3) |
| **2** | 🔜 Next | Transform layer — clean, validate, deduplicate |
| **3** | 📅 Planned | Salesforce sync — push clean data to CRM |
| **4** | 📅 Planned | Scheduling (Airflow), alerting, CI/CD |

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ValueError: STRIPE_API_KEY is missing` | `.env` not filled in | Copy `.env.example` → `.env` and add your key |
| `401 Unauthorized` from Stripe | Wrong or expired API key | Check your key at dashboard.stripe.com/apikeys |
| `ValueError: STORAGE_BACKEND is 's3' but AWS_BUCKET_NAME is missing` | S3 mode but AWS creds missing | Either set `STORAGE_BACKEND=local` or add AWS credentials |
| `ModuleNotFoundError` | venv not activated or deps not installed | Run `source venv/bin/activate && pip install -r requirements.txt` |
| `0 customers found` | Stripe test account is empty | Run `python scripts/seed_stripe_test_data.py` |

---

## Security Rules for the Team

| ✅ Do | ❌ Never |
|---|---|
| Use `sk_test_...` keys locally | Commit `.env` to git |
| Keep your AWS keys personal | Share secret keys over Slack/email |
| Use `STORAGE_BACKEND=local` for dev | Use live Stripe keys on local machine |
| Rotate keys if accidentally exposed | Push `data/` folder to git |

---

> 📬 **Questions?** Reach out to **Siddhatej Dahale** — branch owner: `siddhatej-dahale`
