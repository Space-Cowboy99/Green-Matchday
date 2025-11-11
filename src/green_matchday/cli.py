from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path
from .engine import estimate_fixture


log = logging.getLogger("green_matchday")


def _default_clubs_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "data" / "clubs.csv"


def _default_factors_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "data" / "factors.yaml"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="green-matchday")
    sub = p.add_subparsers(dest="cmd", required=True)

    est = sub.add_parser("estimate", help="Estimate one fixture")
    est.add_argument("home")
    est.add_argument("away")
    est.add_argument("--clubs", type=Path, default=_default_clubs_path())
    est.add_argument("--factors", type=Path, default=_default_factors_path())
    est.add_argument("--away-fans", type=int, default=3000)
    est.add_argument("--out", type=Path, help="Write result to JSON file")
    est.add_argument("--format", choices=["text", "json"], default="text")
    est.add_argument("--pretty", action="store_true")


    bat = sub.add_parser("batch", help="Estimate many fixtures from a CSV")
    bat.add_argument("fixtures", type=Path, help="CSV with columns: home,away,away_fans")
    bat.add_argument("--clubs", type=Path, default=_default_clubs_path())
    bat.add_argument("--factors", type=Path, default=_default_factors_path())
    bat.add_argument("--out-json", type=Path, help="Write all results to JSON")
    bat.add_argument("--out-csv", type=Path, help="Write all results to CSV")

    return p

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "estimate":
        res = estimate_fixture(
            args.home,
            args.away,
            str(args.clubs),
            away_fans=args.away_fans,
            factors_path=str(args.factors),
        )

        payload = res if isinstance(res, dict) else getattr(res, "__dict__", res)

        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(payload, indent=2))
        else:
            if args.format == "json":
                print(json.dumps(payload, indent=2 if args.pretty else None))
            else:
                print(f"Fixture: {args.home} vs {args.away}")
                print(f"Distance (km): {payload.get('distance_km')}")
                print(f"Per-fan kgCO2e: {payload.get('per_fan_kg')}")
                print(f"Total kgCO2e: {payload.get('total_kg')}")
                ms = (payload.get("assumptions") or {}).get("mode_share") or {}
                if ms:
                    print("Mode share:", ms)

    elif args.cmd == "batch":
        results = []
        with args.fixtures.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                home = row["home"].strip()
                away = row["away"].strip()
                away_fans = int(row.get("away_fans", 3000))
                r = estimate_fixture(
                    home,
                    away,
                    str(args.clubs),
                    away_fans=away_fans,
                    factors_path=str(args.factors),
                )
                payload = r if isinstance(r, dict) else getattr(r, "__dict__", r)
                payload.update({"home": home, "away": away, "away_fans": away_fans})
                results.append(payload)

        if args.out_json:
            args.out_json.write_text(json.dumps(results, indent=2))
        if args.out_csv:
            fieldnames = sorted({k for d in results for k in d.keys()})
            with args.out_csv.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                w.writerows(results)
        if not args.out_json and not args.out_csv:
            print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()

