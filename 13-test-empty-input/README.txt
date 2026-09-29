Commit 13 — test: verify load_records handles empty input

File to edit:
  tests/test_database.py

What changed:
  - implemented test_load_records_empty_list_returns_zero, which checks
    that load_records([]) short-circuits and returns 0 without touching
    the DB (this matters because pg_insert(...).values([]) would error)

Commit message:
  test: verify load_records handles empty input

Run `pytest` before committing to confirm it actually passes.
