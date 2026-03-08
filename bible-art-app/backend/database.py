"""SQLite database helpers for the Bible Art App."""

import sqlite3
from pathlib import Path

from models import SCHEMA_SQL

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "bible_art.db"


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row dictionaries enabled."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they do not exist."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DB_PATH}")
