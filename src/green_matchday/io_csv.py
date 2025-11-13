# src/green_matchday/io_csv.py
from __future__ import annotations
from pathlib import Path
import csv
from typing import Any, Dict, List

def ensure_out(out_dir: str | Path) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    return out

def write_per_mode_csv(results: List[Dict[str, Any]], out_dir: str | Path = "out", filename: str = "batch.csv") -> Path:
    """
    Writes one row per (fixture, mode). Expects each fixture dict to have a "modes" list.
    Falls back gracefully if some keys are missing.
    """
    out = ensure_out(out_dir)
    path = out / filename

    # Minimal, tolerant columns
    base_cols = ["fixture_id", "home", "away", "date", "band"]
    mode_cols = ["mode", "travellers", "distance_km", "emissions_kg", "share"]
    fieldnames = base_cols + mode_cols

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for fx in results:
            base = {k: fx.get(k, "") for k in base_cols}
            modes = fx.get("modes", [])
            if not isinstance(modes, list) or not modes:
                # Write a single row with blanks if no modes present
                w.writerow(base | {k: "" for k in mode_cols})
                continue
            for m in modes:
                row = base | {
                    "mode": m.get("name", m.get("mode", "")),
                    "travellers": m.get("travellers", ""),
                    "distance_km": m.get("distance_km", ""),
                    "emissions_kg": m.get("emissions_kg", ""),
                    "share": m.get("share", ""),
                }
                w.writerow(row)
    return path

