from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Iterable
import pandas as pd

from .config import PLAYERS_CSV, matches_csv_url
from .download import fetch_to_cache

@dataclass(frozen=True)
class Player:
    player_id: int
    name: str

def load_players() -> pd.DataFrame:
    path = fetch_to_cache("players", PLAYERS_CSV, "atp_players.csv")
    df = pd.read_csv(path, low_memory=False)

    # Support both historical schemas:
    # old: first_name, last_name, country_code, birth_date
    # new: name_first, name_last, ioc, dob, wikidata_id
    if "first_name" in df.columns and "last_name" in df.columns:
        first = df["first_name"].fillna("")
        last = df["last_name"].fillna("")
    elif "name_first" in df.columns and "name_last" in df.columns:
        first = df["name_first"].fillna("")
        last = df["name_last"].fillna("")
    else:
        raise KeyError(
            "Could not find name columns in atp_players.csv. "
            f"Columns available: {list(df.columns)}"
        )

    df["name"] = (first.astype(str) + " " + last.astype(str)).str.strip()
    df = df[df["name"].str.len() > 0].copy()
    return df


def load_matches(year: int) -> pd.DataFrame:
    url = matches_csv_url(year)
    path = fetch_to_cache(f"matches_{year}", url, f"atp_matches_{year}.csv")
    df = pd.read_csv(path, low_memory=False)
    # Normalize commonly used columns
    # Surface can be NaN for some entries; keep as is and filter later
    # best_of is int in most years but can be float; coerce
    if "best_of" in df.columns:
        df["best_of"] = pd.to_numeric(df["best_of"], errors="coerce").astype("Int64")
    df["tourney_date"] = pd.to_numeric(df.get("tourney_date", pd.NA), errors="coerce").astype("Int64")
    return df

def ensure_years_loaded(years: Iterable[int]) -> Dict[int, pd.DataFrame]:
    out = {}
    for y in sorted(set(int(x) for x in years)):
        out[y] = load_matches(y)
    return out
