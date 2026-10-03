# ETL Pipeline — Week 1 & Week 2

This branch (`week1-and-week2`) contains the **complete combined work** of Week 1 and Week 2 of the ETL Pipeline project.

---

## 📅 Week 1 — Extract & Load  _(Siddhatej Dahale)_

| Module | Description |
|--------|-------------|
| `src/extractors/stripe_extractor.py` | Pull all customers from Stripe API with full pagination |
| `src/extractors/base.py` | Abstract base class for all future extractors |
| `src/models/customer.py` | Pydantic model validating the Stripe customer shape |
| `src/loaders/local_loader.py` | Save raw JSON to local disk (Hive-partitioned) |
| `src/loaders/s3_loader.py` | Upload raw JSON to AWS S3 (same interface) |
| `src/config.py` | Load & validate all `.env` settings at startup |
| `src/utils/logger.py` | JSON-structured logging (machine-parseable) |
| `src/utils/retry.py` | Auto-retry on 429 / 5xx errors with exponential backoff |
| `src/main.py` | Pipeline orchestrator: Extract → Load |
| `scripts/seed_stripe_test_data.py` | Seed Stripe test account with dummy customers |

**Week 1 Output:** Raw customer JSON saved to:
```
data/raw/stripe/customers/year=YYYY/month=MM/day=DD/<run-id>/data.json
```

---

## 📅 Week 2 — Transform & Validate  _(Bhoomi)_

| Module | Description |
|--------|-------------|
| `src/transformers/mapper.py` | Convert `Customer` Pydantic object → plain dict |
| `src/transformers/cleaner.py` | Trim whitespace, blank strings → `None` |
| `src/transformers/normalizer.py` | Email → lowercase, currency → lowercase, Unix → ISO timestamp |
| `src/transformers/transformer.py` | Orchestrate the full transform pipeline |
| `src/validators/validator.py` | Quality gate: enforce id, email, currency, created rules |
| `docs/transformation-contract.md` | Full specification of the transformation layer |

**Week 2 Transform Pipeline:**
```
Customer (Pydantic model)
    ↓  mapper      → plain dict
    ↓  cleaner     → trimmed, no blank strings
    ↓  normalizer  → email lowercase, currency lowercase, created ISO string
    ↓  validator   → quality gate (raises on invalid)
    ↓
Canonical record ✅ ready for data warehouse
```

---

## 🧪 Test Coverage — 26 Tests, All Passing

```
tests/test_cleaner.py          2 tests  — string trimming & blank → None
tests/test_normalizer.py       3 tests  — email, currency, timestamp
tests/test_transformer.py      1 test   — end-to-end transform pipeline
tests/test_validator.py        4 tests  — id required, currency 3-char, etc.
tests/test_stripe_extractor.py 7 tests  — pagination, empty, invalid records
tests/test_s3_loader.py        6 tests  — S3 key format, manifest fields
```

Run all tests:
```bash
cd ETL_Pipeline_Project
source venv/bin/activate
pytest -v
```

---

## 🚀 How to Run the Pipeline

```bash
# 1. Clone & setup
git clone https://github.com/siddhatejdahale03-arch/ETL-Pipeline-project.git
cd ETL-Pipeline-project
git checkout week1-and-week2
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Add your STRIPE_API_KEY to .env

# 3. Run
cd src
python main.py
```

---

## 📁 Combined Folder

The `combined/` folder shows both branches' work side by side:
```
combined/
├── siddhatej/   ← Week 1: Extractors, Loaders, Models, Utils
└── bhoomi/      ← Week 2: Transformers, Validators, Docs, Tests
```
