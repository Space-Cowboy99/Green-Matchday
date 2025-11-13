from __future__ import annotations

from .io_csv import write_per_mode_csv
from .io_json import write_batch_json
from pathlib import Path

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

        # Save results for a single fixture
        write_per_mode_csv([res], out_dir="out", filename="single.csv")
        write_batch_json([res], out_dir="out", filename="single.json")
        print("✅ Saved outputs to 'out/single.csv' and 'out/single.json'")

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
                
                ass = (payload.get("assumptions") or {})
                per_mode = ass.get("per_mode_kg", {})
                for mode, kg in per_mode.items():
                    payload[f"{mode}_kg_per_fan"] = kg

                results.append(payload)

                # ---- AFTER the for-loop that builds `results` and the final `results.append(payload)` ----

                # Decide where to write JSON
                if args.out_json:
                    json_dir = args.out_json.parent
                    json_name = args.out_json.name
                else:
                    json_dir = Path("out")
                    json_name = "batch.json"

                # Decide where to write CSV
                if args.out_csv:
                    csv_dir = args.out_csv.parent
                    csv_name = args.out_csv.name
                else:
                    csv_dir = Path("out")
                    csv_name = "batch.csv"

                # Write both files using the helpers
                write_per_mode_csv(results, out_dir=csv_dir, filename=csv_name)
                write_batch_json(results, out_dir=json_dir, filename=json_name)

                print(f"✅ Saved: {csv_dir / csv_name}")
                print(f"✅ Saved: {json_dir / json_name}")
        
        # ---- summary ----
        total_kg = sum(p.get("total_kg", 0) for p in results)
        print("\nSUMMARY:")
        print(f"  Total emissions across {len(results)} fixtures: {round(total_kg, 1):,} kg CO₂e")

        # optional per-mode share
        mode_totals = {}
        for p in results:
            for k, v in (p.get("assumptions") or {}).get("per_mode_kg", {}).items():
                mode_totals[k] = mode_totals.get(k, 0) + v * p.get("away_fans", 0)

        for k, v in mode_totals.items():
            pct = 100 * v / total_kg if total_kg else 0
            print(f"  {k:<6}: {round(v,1):,} kg ({pct:.1f}%)")

        # ---- per-fixture summaries ----
        print("\nDETAILED BREAKDOWN BY FIXTURE:")
        for p in results:
            home, away = p.get("home"), p.get("away")
            total = p.get("total_kg", 0)
            print(f"\n{home} vs {away}")
            print(f"  Total emissions: {round(total,1):,} kg CO₂e")
            per_mode = (p.get("assumptions") or {}).get("per_mode_kg", {})
            for k, v in per_mode.items():
                pct = 100 * (v * p.get("away_fans", 0)) / total if total else 0
                print(f"  {k:<6}: {round(v * p.get('away_fans',0),1):,} kg ({pct:.1f}%)")


if __name__ == "__main__":
    main()

