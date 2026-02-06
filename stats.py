from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass
class SeasonStats:
    matches: int
    wins: int
    losses: int
    win_pct: float
    titles: int | None
    finals: int | None

def compute_season_stats(matches: pd.DataFrame, player_name: str, *, surface: str, best_of: int | None) -> SeasonStats | None:
    df = matches.copy()
    if "surface" not in df.columns:
        return None
    df = df[df["surface"].fillna("").astype(str).str.lower() == surface.lower()]
    if df.empty:
        return None
    if best_of is not None and "best_of" in df.columns:
        df2 = df[df["best_of"].fillna(pd.NA) == best_of]
        if len(df2) >= 50:
            df = df2

    # Player matches
    mask_w = df["winner_name"] == player_name
    mask_l = df["loser_name"] == player_name
    dfp = df[mask_w | mask_l].copy()
    if dfp.empty:
        return None
    wins = int(mask_w[dfp.index].sum())
    losses = int(mask_l[dfp.index].sum())
    total = wins + losses
    win_pct = wins / total if total else 0.0

    # Titles/finals (approx): count tournaments where player reached F as winner/loser
    titles = finals = None
    if "round" in dfp.columns and "tourney_id" in dfp.columns:
        finals_df = dfp[dfp["round"].astype(str).str.upper() == "F"]
        if not finals_df.empty:
            finals = int(finals_df["tourney_id"].nunique())
            titles = int(finals_df[finals_df["winner_name"] == player_name]["tourney_id"].nunique())

    return SeasonStats(matches=total, wins=wins, losses=losses, win_pct=win_pct, titles=titles, finals=finals)
