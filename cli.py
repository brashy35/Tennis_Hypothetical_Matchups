from __future__ import annotations
import sys
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.validation import Validator, ValidationError

from .data import load_players
from .core import run_compare
from .model import SURFACE_MAP

def _int_validator(min_v: int, max_v: int) -> Validator:
    def _validate(text: str) -> None:
        try:
            v = int(text)
        except ValueError:
            raise ValidationError(message="Enter a number.")
        if v < min_v or v > max_v:
            raise ValidationError(message=f"Enter a year between {min_v} and {max_v}.")
    return Validator.from_callable(lambda t: (_validate(t), True)[1], error_message="Invalid number", move_cursor_to_end=True)

def main() -> None:
    players_df = load_players()
    names = players_df["name"].dropna().astype(str).unique().tolist()
    completer = FuzzyWordCompleter(names, WORD=True)

    # Infer year bounds from files typically available (1968..current-ish)
    min_year, max_year = 1968, 2030

    print("\nTennis Compare (interactive)\n")

    p1 = prompt("Player A: ", completer=completer)
    y1 = prompt("Year A: ", validator=_int_validator(min_year, max_year), validate_while_typing=False)
    p2 = prompt("Player B: ", completer=completer)
    y2 = prompt("Year B: ", validator=_int_validator(min_year, max_year), validate_while_typing=False)

    surfaces = ["Hard", "Clay", "Grass", "Indoor"]
    surf_comp = FuzzyWordCompleter(surfaces, WORD=True)
    surface = prompt("Surface (Hard/Clay/Grass/Indoor): ", completer=surf_comp).strip() or "Hard"
    if surface.lower() in SURFACE_MAP:
        surface = SURFACE_MAP[surface.lower()]

    bo = prompt("Best of (3 or 5): ", validator=Validator.from_callable(lambda t: t.strip() in {"3","5"}, error_message="Enter 3 or 5"), validate_while_typing=False)

    try:
        res = run_compare(p1, int(y1), p2, int(y2), surface, int(bo))
    except Exception as e:
        print(f"\nError: {e}\n")
        sys.exit(1)

    print("\n" + "="*60)
    print(f"{res.player_a} ({res.year_a}) vs {res.player_b} ({res.year_b})")
    print(f"Surface: {res.surface} | BO{res.best_of}")
    print("-"*60)
    print(f"Win Probability: {res.player_a}: {res.p_a_wins:.3f} | {res.player_b}: {1-res.p_a_wins:.3f}")
    if res.elo_a is not None and res.elo_b is not None:
        print(f"Elo (slice): {res.player_a}: {res.elo_a:.1f} ({res.elo_matches_a} matches) | {res.player_b}: {res.elo_b:.1f} ({res.elo_matches_b} matches)")
    print("-"*60)

    def fmt_stats(label: str, s: dict | None) -> str:
        if not s:
            return f"{label}: N/A"
        parts = [
            f"{label}: {s['wins']}-{s['losses']} ({s['win_pct']*100:.1f}%)",
        ]
        if s.get("titles") is not None:
            parts.append(f"Titles: {s['titles']}, Finals: {s['finals']}")
        return " | ".join(parts)

    print(fmt_stats(res.player_a, res.stats_a))
    print(fmt_stats(res.player_b, res.stats_b))


    print("\n" + "="*60)
    print(f"Winner — {res.winner}")
    print("="*60)
    print(f"Confidence: {abs(p_a - 0.5)*200:.1f}%")

    if res.notes:
        print("\nNotes:")
        for n in res.notes:
            print(f"- {n}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
