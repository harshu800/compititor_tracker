"""
One-off DB bootstrap for local trial mode ONLY (SQLite, no Alembic).
Real deployments use Postgres + `alembic upgrade head` — see README.
Run with: python scripts/create_sqlite_db.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine
from app import models  # noqa: F401 - registers all tables on Base.metadata

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print(f"✓ Created {len(Base.metadata.tables)} tables at {engine.url}")
