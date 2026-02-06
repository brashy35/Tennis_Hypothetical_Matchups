from __future__ import annotations
import os
from pathlib import Path

APP_NAME = "tennis-compare"
DEFAULT_CACHE_DIR = Path(os.environ.get("TENNIS_COMPARE_CACHE", Path.home() / f".{APP_NAME}"))
DEFAULT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_DB_PATH = DEFAULT_CACHE_DIR / "cache.sqlite3"
CACHE_DATA_DIR = DEFAULT_CACHE_DIR / "data"
CACHE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Jeff Sackmann tennis_atp raw base
RAW_BASE = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master"
PLAYERS_CSV = f"{RAW_BASE}/atp_players.csv"

def matches_csv_url(year: int) -> str:
    return f"{RAW_BASE}/atp_matches_{year}.csv"
