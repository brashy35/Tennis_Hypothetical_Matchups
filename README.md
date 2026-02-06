# Tennis Compare (CLI + GUI)

A small app that compares two ATP players from specific seasons on a chosen surface and match format (BO3/BO5),
then outputs a win probability plus season stats.

**Data source:** Jeff Sackmann's `tennis_atp` match results (downloaded on-demand and cached locally).  
Repo: https://github.com/JeffSackmann/tennis_atp

## Quickstart

### 1) Create a venv & install deps
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run the interactive CLI
```bash
python -m tennis_compare.cli
```

### 3) Run the GUI
```bash
python -m tennis_compare.gui
```

## Notes
- This MVP uses **surface-specific Elo** built from matches in the selected year+surface(+best-of) slice.
- If there's not enough data for a slice, the app will say so and fall back to broader data (year+surface without best-of).
- The dataset includes many match-level stats fields for modern years, but coverage varies; this MVP focuses on results-based stats.
