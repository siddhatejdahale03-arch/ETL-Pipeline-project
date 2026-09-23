Commit 5 — feat: add script to initialize warehouse tables

Files to add:
  src/database/loader.py   (just create_tables() for now)
  scripts/init_db.py

What to do:
  1. Add these two files.
  2. Confirm it actually runs against a local Postgres instance:
     python scripts/init_db.py
  3. Check the `transactions` table exists in your local DB before committing.

Commit message:
  feat: add script to initialize warehouse tables
