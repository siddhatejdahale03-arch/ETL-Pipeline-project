Commit 11 — feat: add logging for insert/upsert operations

File to edit:
  src/database/loader.py

What changed:
  - insert_records() now logs a success line with the row count
  - load_records() now logs a success line with the row count
  - (failure paths already logged via logger.exception since commit 9)

Commit message:
  feat: add logging for insert/upsert operations
