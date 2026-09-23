Commit 6 — fix: correct field types based on Stripe/Salesforce docs

File to edit:
  src/database/models.py

What changed from commit 4:
  - currency tightened to String(3) (ISO 4217 codes)
  - explicit nullable=True/False per field, based on what Stripe/Salesforce
    docs actually guarantee vs. optional
  - added updated_at and is_synced, which the draft missed
  - added a docstring + revision-history comment block

Commit message:
  fix: correct field types based on Stripe/Salesforce docs
