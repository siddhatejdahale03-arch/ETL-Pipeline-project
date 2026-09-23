Commit 3 — feat: add SQLAlchemy engine and session setup

File to add:
  src/database/db.py   (src/database/__init__.py too, so it's a package)

What to do:
  1. Create the src/database/ folder, add these files.
  2. Make sure DATABASE_URL is set in your .env (from commit 2) and loaded
     into the environment before running anything that imports this module.

Commit message:
  feat: add SQLAlchemy engine and session setup

Note: config.py doesn't exist yet — DATABASE_URL is read directly with
os.getenv() here. You'll refactor this into config.py at commit 17.
