import csv
import math
from dataclasses import dataclass
from typing import Dict, Tuple

# ---------------------------
# Basics: distance + factors
# ---------------------------

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
    mode_share: Dict[str, float] = None,
    factors: Dict[str, float] = None,
) -> Result:
    """
    Basic estimate:
      per_fan = distance_km * sum(mode_share[m] * factors[m])
      total = per_fan * away_fans
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
    distance = haversine_km(h_lat, h_lon, a_lat, a_lon)

    factors = factors or DEFAULT_FACTORS_KG_PER_PKM
    mode_share = mode_share or {"train": 0.5, "coach": 0.3, "car": 0.2}
    ms = _normalise_mode_share(mode_share)

    # Only use modes that exist in factors
    effective = sum((ms.get(m, 0.0) * factors.get(m, 0.0)) for m in ms.keys())

    per_fan = distance * effective
    total = per_fan * away_fans

    return Result(
        distance_km=round(distance, 3),
        per_fan_kg=round(per_fan, 3),
        total_kg=round(total, 0),
        assumptions={
            "away_fans": away_fans,
            "mode_share": ms,
            "factors_kg_per_pkm": factors,
        },
    )
