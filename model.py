from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import math
import pandas as pd

SURFACE_MAP = {
    "hard": "Hard",
    "clay": "Clay",
    "grass": "Grass",
    "indoor": "Indoor",
    "carpet": "Carpet",
}

@dataclass
class SliceInfo:
    year: int
    surface: str
    best_of: int | None

@dataclass
class EloResult:
    elo: float
    matches_used: int

def _expected(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(elo_a - elo_b) / 400.0))

def _k_factor(round_name: str | None) -> float:
    # Simple heuristic: later rounds carry slightly more weight
    if not round_name:
        return 32.0
    r = round_name.upper()
    if r in {"F"}:
        return 40.0
    if r in {"SF"}:
        return 36.0
    if r in {"QF"}:
        return 34.0
    return 32.0

def compute_elo_for_slice(matches: pd.DataFrame, player_name: str, *, surface: str, best_of: int | None) -> EloResult | None:
    """Compute end-of-slice Elo for a single player using only slice matches.
    Starts everyone at 1500 within the slice (so it's a within-slice strength estimate).
    """
    df = matches.copy()

    # Filter surface
    target_surface = SURFACE_MAP.get(surface.lower(), surface)
    if "surface" in df.columns:
        df = df[df["surface"].fillna("").astype(str).str.lower() == target_surface.lower()]
    else:
        return None

    # Filter best-of if requested and data exists
    if best_of is not None and "best_of" in df.columns:
        df2 = df[df["best_of"].fillna(pd.NA) == best_of]
        # If too few matches, fall back to surface-only
        if len(df2) >= 50:
            df = df2

    if df.empty:
        return None

    # Keep only matches involving the player (as winner or loser)
    mask = (df["winner_name"] == player_name) | (df["loser_name"] == player_name)
    df = df[mask].copy()
    if df.empty:
        return None

    # Sort by tourney_date then match_num if available
    sort_cols = []
    if "tourney_date" in df.columns:
        sort_cols.append("tourney_date")
    if "match_num" in df.columns:
        sort_cols.append("match_num")
    if sort_cols:
        df = df.sort_values(sort_cols)

    # Elo within this slice: rating dict for opponents we encounter
    ratings: Dict[str, float] = {}
    def get_r(name: str) -> float:
        return ratings.get(name, 1500.0)
    def set_r(name: str, v: float) -> None:
        ratings[name] = v

    used = 0
    for _, row in df.iterrows():
        w = row.get("winner_name")
        l = row.get("loser_name")
        if not isinstance(w, str) or not isinstance(l, str):
            continue
        rw, rl = get_r(w), get_r(l)
        ew = _expected(rw, rl)
        k = _k_factor(row.get("round"))
        rw_new = rw + k * (1 - ew)
        rl_new = rl + k * (0 - (1 - ew))
        set_r(w, rw_new)
        set_r(l, rl_new)
        used += 1

    return EloResult(elo=get_r(player_name), matches_used=used)

def match_win_prob_from_elos(elo_a: float, elo_b: float) -> float:
    return _expected(elo_a, elo_b)

def adjust_for_best_of(p_match: float, best_of: int) -> float:
    """Adjust match win probability for BO3 vs BO5 assuming iid sets approximation."""
    p = max(1e-6, min(1 - 1e-6, p_match))
    if best_of == 3:
        return (p ** 2) * (3 - 2 * p)
    if best_of == 5:
        return (p ** 3) * (10 - 15 * p + 6 * (p ** 2))
    return p
