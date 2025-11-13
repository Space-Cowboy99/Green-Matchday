# src/green_matchday/io_json.py
from pathlib import Path
import json
from typing import Any, List

def ensure_out(out_dir: str | Path) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    return out

def write_batch_json(results: List[dict[str, Any]], out_dir: str | Path = "out", filename: str = "batch.json") -> Path:
    out = ensure_out(out_dir)
    path = out / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return path

