Commit 10 — feat: implement upsert logic for incremental loads

File to edit:
  src/database/loader.py

What changed:
  - added load_records(): builds a Postgres INSERT ... ON CONFLICT DO
    UPDATE statement so re-running a load updates existing rows
    (matched on id) instead of erroring or duplicating
  - update_cols is built dynamically from the model's columns, minus id,
    so it stays correct if the schema changes later

Commit message:
  feat: implement upsert logic for incremental loads
