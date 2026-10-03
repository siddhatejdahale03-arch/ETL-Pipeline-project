# Combined Branch — Siddhatej + Bhoomi

This folder represents the **merged contributions** from two team branches:

| Subfolder | Branch | Contributor | Contents |
|-----------|--------|-------------|----------|
| `siddhatej/` | `Siddhatej-Dahale` | Siddhatej Dahale | Extractors, Loaders, Models, Utils, Scripts, Main pipeline |
| `bhoomi/` | `Bhoomi` | Bhoomi | Transformers, Validators, Transformation contract docs, Tests |

---

## What Each Branch Contributed

### 🔷 Siddhatej — Extraction & Loading Layer
- **`siddhatej/extractors/`** — Stripe extractor with base class
- **`siddhatej/loaders/`** — Local & S3 loaders
- **`siddhatej/models/`** — Customer Pydantic model
- **`siddhatej/utils/`** — Logger & Retry utilities
- **`siddhatej/scripts/`** — Stripe test data seeder
- **`siddhatej/main.py`** — Pipeline entry point
- **`siddhatej/config.py`** — Environment config

### 🔶 Bhoomi — Transformation & Validation Layer
- **`bhoomi/transformers/`** — Cleaner, Mapper, Normalizer, Transformer pipeline
- **`bhoomi/validators/`** — Customer record validator
- **`bhoomi/transformation-contract.md`** — Full transformation specification
- **`bhoomi/test_cleaner.py`** — Unit tests for cleaner
- **`bhoomi/test_normalizer.py`** — Unit tests for normalizer
- **`bhoomi/test_transformer.py`** — Integration tests for full pipeline
- **`bhoomi/test_validator.py`** — Unit tests for validator

---

## Combined ETL Flow

```
Stripe API
    ↓
[Siddhatej] StripeExtractor  →  Customer (Pydantic model)
    ↓
[Bhoomi]    Transformer      →  clean_customer_data()
                             →  normalize_customer_data()
                             →  ensure_valid_customer_record()
    ↓
[Siddhatej] Loader           →  LocalLoader / S3Loader
    ↓
Data Warehouse / S3
```

---

> Merged via: `git merge origin/Bhoomi` into `siddhatej-dahale` branch (zero conflicts).
