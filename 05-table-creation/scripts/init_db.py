"""
Run this once to create warehouse tables locally.
Owner: Rohan (Data Loading & Warehouse Development)

Usage:
    python scripts/init_db.py
"""
from src.database.loader import create_tables

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully.")
