"""
Database engine and session setup.

Uses the DATABASE_URL from app.core.config (SQLite by default, see
.env.example). Kept intentionally simple for Phase 3 — one engine, one
session factory, no connection pooling tuning or multi-database setup.

A relative sqlite path (e.g. "sqlite:///./data/app.db") is resolved
against the project root rather than the process's current working
directory, so the database always lands in the top-level data/ folder
that Phase 1 already set up — regardless of whether uvicorn is started
from the project root or from backend/.
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# backend/app/db/database.py -> parents[3] is the project root
# (ipo-research-platform/), i.e. the parent of backend/.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _resolve_database_url(url: str) -> str:
    """Turn a relative sqlite:///./data/app.db URL into an absolute one
    anchored at the project root. Leaves non-sqlite or already-absolute
    URLs untouched."""
    prefix = "sqlite:///./"
    if not url.startswith(prefix):
        return url
    relative_path = url[len(prefix):]
    absolute_path = (PROJECT_ROOT / relative_path).resolve()
    return f"sqlite:///{absolute_path}"


DATABASE_URL = _resolve_database_url(settings.database_url)

# SQLite needs check_same_thread=False when used with FastAPI's threaded
# request handling. This has no effect for other database URLs.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_sqlite_dir_exists():
    """Create the folder for the SQLite file (e.g. <project root>/data) if
    it's missing."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    db_path = DATABASE_URL.replace("sqlite:///", "", 1)
    directory = os.path.dirname(db_path)
    if directory:
        Path(directory).mkdir(parents=True, exist_ok=True)


def init_db():
    """Create the SQLite file/folder and all tables if they don't exist yet."""
    _ensure_sqlite_dir_exists()
    # Import models here so they're registered on Base before create_all runs.
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Safe migration: ensure new columns exist in existing SQLite database
    if DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check existing columns in drhp_documents
            res = conn.execute(text("PRAGMA table_info(drhp_documents)")).fetchall()
            existing_cols = {row[1] for row in res}
            if existing_cols:
                if "source_url" not in existing_cols:
                    conn.execute(text("ALTER TABLE drhp_documents ADD COLUMN source_url VARCHAR(500)"))
                if "source_name" not in existing_cols:
                    conn.execute(text("ALTER TABLE drhp_documents ADD COLUMN source_name VARCHAR(100)"))
            conn.commit()
