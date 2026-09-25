Commit 9 — fix: add error handling and rollback to insert

File to edit:
  src/database/loader.py

What changed:
  - wrapped insert_records() body in try/except/finally
  - on failure: session.rollback(), log the exception, re-raise
  - session.close() moved into finally so it always runs

Commit message:
  fix: add error handling and rollback to insert
