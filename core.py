from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
import pandas as pd

from .data import load_players, load_matches
from .names import resolve_player
from .model import compute_elo_for_slice, match_win_prob_from_elos, adjust_for_best_of, SURFACE_MAP
from .stats import compute_season_stats

@dataclass
class CompareResult:
    player_a: str
    player_b: str
    year_a: int
    year_b: int
    surface: str
    best_of: int
    p_a_wins: float
    elo_a: float | None
    elo_b: float | None
    elo_matches_a: int | None
    elo_matches_b: int | None
    stats_a: dict | None
    stats_b: dict | None
    notes: list[str]
    winner: str

def run_compare(player_a_raw: str, year_a: int, player_b_raw: str, year_b: int, surface: str, best_of: int) -> CompareResult:
    notes: list[str] = []
    players_df = load_players()

    pa, alts_a = resolve_player(players_df, player_a_raw)
    pb, alts_b = resolve_player(players_df, player_b_raw)
    if not pa:
        raise ValueError(f"Could not resolve Player A: '{player_a_raw}'. Suggestions: {alts_a}")
    if not pb:
        raise ValueError(f"Could not resolve Player B: '{player_b_raw}'. Suggestions: {alts_b}")

    # Normalize surface to dataset casing
    surface_norm = SURFACE_MAP.get(surface.lower(), surface)
    # Load year match files
    ma = load_matches(int(year_a))
    mb = load_matches(int(year_b))

    # Elo per slice
    elo_a_res = compute_elo_for_slice(ma, pa, surface=surface_norm, best_of=best_of)
    elo_b_res = compute_elo_for_slice(mb, pb, surface=surface_norm, best_of=best_of)

    if not elo_a_res:
        notes.append(f"Not enough slice data for {pa} ({year_a}, {surface_norm}, BO{best_of}) — Elo unavailable.")
    if not elo_b_res:
        notes.append(f"Not enough slice data for {pb} ({year_b}, {surface_norm}, BO{best_of}) — Elo unavailable.")

    # If either Elo missing, fall back to surface-only Elo (ignore BO filter)
    if (not elo_a_res) or (not elo_b_res):
        if not elo_a_res:
            elo_a_res = compute_elo_for_slice(ma, pa, surface=surface_norm, best_of=None)
            if elo_a_res:
                notes.append(f"Fallback: used {pa} ({year_a}, {surface_norm}) without best-of filter.")
        if not elo_b_res:
            elo_b_res = compute_elo_for_slice(mb, pb, surface=surface_norm, best_of=None)
            if elo_b_res:
                notes.append(f"Fallback: used {pb} ({year_b}, {surface_norm}) without best-of filter.")

    elo_a = float(elo_a_res.elo) if elo_a_res else None
    elo_b = float(elo_b_res.elo) if elo_b_res else None

    # Probability
    if elo_a is not None and elo_b is not None:
        p_match = match_win_prob_from_elos(elo_a, elo_b)
        p_a = adjust_for_best_of(p_match, best_of)
    else:
        p_a = 0.5
        notes.append("Probability fallback: missing Elo for one or both players, returning 0.50.")

    if p_a >= 0.60:
        winner = pa
    elif p_a <= 0.40:
        winner = pb
    else:
        winner = "Too close to call"


    # Stats (season aggregates)
    sa = compute_season_stats(ma, pa, surface=surface_norm, best_of=best_of)
    sb = compute_season_stats(mb, pb, surface=surface_norm, best_of=best_of)
    stats_a = sa.__dict__ if sa else None
    stats_b = sb.__dict__ if sb else None
    if not sa:
        notes.append(f"Season stats unavailable for {pa} in {year_a} on {surface_norm} (BO filter may be too strict).")
    if not sb:
        notes.append(f"Season stats unavailable for {pb} in {year_b} on {surface_norm} (BO filter may be too strict).")

    return CompareResult(
        player_a=pa, player_b=pb, year_a=int(year_a), year_b=int(year_b),
        surface=surface_norm, best_of=int(best_of),
        p_a_wins=float(p_a),
        elo_a=elo_a, elo_b=elo_b,
        elo_matches_a=int(elo_a_res.matches_used) if elo_a_res else None,
        elo_matches_b=int(elo_b_res.matches_used) if elo_b_res else None,
        stats_a=stats_a, stats_b=stats_b,
        notes=notes,
        winner=winner,
    )
