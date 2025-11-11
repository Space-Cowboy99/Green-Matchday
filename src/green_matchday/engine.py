import csv
import math
from dataclasses import dataclass
from typing import Dict, Tuple

from pathlib import Path
import json

try:
    import yaml  # pip install PyYAML
except ImportError:
    yaml = None


def _load_factors(path: str | None) -> dict:
    """
    Load factors + mode share from YAML/JSON.
    Falls back to hard-coded defaults if file missing.
    """
    # default to project data/factors.yaml if not provided
    if path is None:
        path = str(Path(__file__).resolve().parents[2] / "data" / "factors.yaml")

    p = Path(path)
    if not p.exists():
        # safe defaults
        return {
            "mode_share": {"default": {"train": 0.5, "coach": 0.3, "car": 0.2}},
            "factors_kg_per_pkm": {"train": 0.041, "coach": 0.027, "car": 0.120},
            "distance": {"km_rounding": 3},
        }

    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        return json.loads(text)

    if yaml is None:
        raise RuntimeError("PyYAML not installed. Run: pip install PyYAML")
    return yaml.safe_load(text)


# ---------------------------
# Basics: distance + factors
# ---------------------------

def _select_mode_share(factors: dict, distance_km: float) -> dict:
    bands = factors.get("mode_share", {}).get("bands")
    if not bands:
        return factors["mode_share"]["default"]
    for band in bands:
        max_km = band.get("max_km")
        if max_km is None or distance_km <= float(max_km):
            return {k: float(v) for k, v in band.items() if k != "max_km"}
    return {k: float(v) for k, v in bands[-1].items() if k != "max_km"}

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 coordinates in km."""
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def _load_clubs_csv(path: str) -> Dict[str, Tuple[float, float]]:
    """Return {club_name_lower: (lat, lon)} from data/clubs.csv."""
    clubs: Dict[str, Tuple[float, float]] = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["club"].strip().lower()
            clubs[name] = (float(row["lat"]), float(row["lon"]))
    return clubs

# Simple in-code defaults for now; later we can parse YAML.
DEFAULT_FACTORS_KG_PER_PKM = {
    "train": 0.041,
    "coach": 0.027,
    "car":   0.120,
    # Flight omitted from default calc unless user supplies it
}

def _normalise_mode_share(ms: Dict[str, float]) -> Dict[str, float]:
    total = sum(v for v in ms.values() if v is not None)
    if total <= 0:
        return {k: 0.0 for k in ms}
    return {k: v / total for k, v in ms.items()}

@dataclass(frozen=True)
class Result:
    distance_km: float
    per_fan_kg: float
    total_kg: float
    assumptions: Dict

def estimate_fixture(
    home: str,
    away: str,
    clubs_csv_path: str = "data/clubs.csv",
    away_fans: int = 3000,
    mode_share: Dict | None = None,
    factors: Dict[str, float] | None = None,
    factors_path: str | None = None,
) -> Result:
    """
    Estimate matchday travel emissions for a fixture.
    """
    if away_fans < 0:
        raise ValueError("away_fans must be >= 0")

    clubs = _load_clubs_csv(clubs_csv_path)
    h_key, a_key = home.strip().lower(), away.strip().lower()
    if h_key not in clubs:
        raise ValueError(f"Unknown club: {home}")
    if a_key not in clubs:
        raise ValueError(f"Unknown club: {away}")

    h_lat, h_lon = clubs[h_key]
    a_lat, a_lon = clubs[a_key]
    distance_km = haversine_km(h_lat, h_lon, a_lat, a_lon)

    if factors_path:
        factors = _load_factors(factors_path)
    if factors is None:
        factors = _load_factors(None)

    if mode_share is None:
        mode_share = _select_mode_share(factors, distance_km)

    factors_kg_per_pkm = factors ["factors_kg_per_pkm"]

    per_mode_kg = {
        m: round(distance_km * mode_share.get(m, 0.0) * float(factors_kg_per_pkm[m]), 3) for m in mode_share.keys()
    }
    per_fan_kg = round(sum(per_mode_kg.values()), 3)
    total_kg = round(per_fan_kg * away_fans, 1)

    assumptions = {
        "away_fans": away_fans,
        "mode_share": mode_share,
        "factors_kg_per_pkm": factors_kg_per_pkm,
        "per_mode_kg": per_mode_kg,
    }

    return Result(
        distance_km=round(distance_km, 3),
        per_fan_kg=per_fan_kg,
        total_kg=total_kg,
        assumptions=assumptions,
    )


