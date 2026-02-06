from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Iterable, Optional, Tuple
from .config import CACHE_DB_PATH

SCHEMA = '''
CREATE TABLE IF NOT EXISTS files(
  key TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  etag TEXT,
  last_modified TEXT,
  fetched_at TEXT NOT NULL
);
'''

def connect(db_path: Path = CACHE_DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute(SCHEMA)
    return con

def get_file_meta(con: sqlite3.Connection, key: str) -> Optional[Tuple[str, Optional[str], Optional[str]]]:
    row = con.execute("SELECT path, etag, last_modified FROM files WHERE key = ?", (key,)).fetchone()
    return row if row else None

def upsert_file_meta(con: sqlite3.Connection, key: str, path: str, etag: str | None, last_modified: str | None, fetched_at: str) -> None:
    con.execute(
        "INSERT INTO files(key, path, etag, last_modified, fetched_at) VALUES(?,?,?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET path=excluded.path, etag=excluded.etag, last_modified=excluded.last_modified, fetched_at=excluded.fetched_at",
        (key, path, etag, last_modified, fetched_at),
    )
    con.commit()
