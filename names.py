from __future__ import annotations
from typing import List, Tuple, Optional
import pandas as pd
from rapidfuzz import process, fuzz

def all_player_names(players_df: pd.DataFrame) -> List[str]:
    return players_df["name"].dropna().astype(str).unique().tolist()

def resolve_player(players_df: pd.DataFrame, raw: str, *, limit: int = 5, min_score: int = 80) -> Tuple[str, List[Tuple[str, int]]]:
    """Return best match + alternatives (name, score). Does not auto-confirm."""
    raw = (raw or "").strip()
    if not raw:
        return "", []
    names = all_player_names(players_df)

    # exact (case-insensitive)
    lower_map = {n.lower(): n for n in names}
    if raw.lower() in lower_map:
        return lower_map[raw.lower()], []

    matches = process.extract(raw, names, scorer=fuzz.WRatio, limit=limit)
    alts = [(m[0], int(m[1])) for m in matches]
    best = alts[0][0] if alts and alts[0][1] >= min_score else ""
    return best, alts
