#!/usr/bin/env python3
"""Generate reproducible, explicitly synthetic biotech inventory CSVs."""
import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AS_OF = date(2026, 10, 9)


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate(seed=42, as_of=DEFAULT_AS_OF, output_dir=None):
    rng = random.Random(seed)
    destination = Path(output_dir) if output_dir else ROOT / "data" / "raw"
    suppliers = [
        {"supplier_id": "S01", "supplier_name": "Harbor Lipid Supply (fictional)", "category": "Specialty ingredients"},
        {"supplier_id": "S02", "supplier_name": "Bay State BioMaterials (fictional)", "category": "Media and buffers"},
        {"supplier_id": "S03", "supplier_name": "New England Sterile Systems (fictional)", "category": "Single-use equipment"},
        {"supplier_id": "S04", "supplier_name": "Cambridge Lab Consumables (fictional)", "category": "Lab consumables"},
    ]
    # name, unit, daily demand, replacement cost/unit, lead days, supplier,
    # released-lot demand-days, expiry offsets. Cases deliberately expose risks.
    profiles = [
        ("Specialty lipid A", "g", 40, 25, 28, "S01", [4, 6, 5], [8, 40, 130]),
        ("Sterile process bags", "each", 12, 52, 21, "S03", [20, 40, 25], [9, 25, 130]),
        ("Buffer salt", "kg", 8, 18, 14, "S02", [8, 15, 35], [20, 80, 130]),
        ("Sucrose excipient", "kg", 5, 20, 30, "S02", [15, 20, 15], [45, 80, 130]),
        ("Sterile vials", "vial", 1500, 0.70, 21, "S04", [3, 4, 3], [30, 80, 130]),
        ("Sterile filters", "each", 10, 85, 35, "S03", [25, 45, 30], [14, 45, 130]),
        ("Process ethanol", "L", 25, 9, 10, "S02", [30, 35, 40], [40, 80, 130]),
        ("Nucleoside ingredient", "g", 15, 42, 42, "S01", [5, 5, 10], [12, 40, 130]),
        ("Single-use tubing", "pack", 8, 120, 25, "S03", [20, 30, 35], [35, 80, 130]),
        ("Growth media", "L", 20, 48, 28, "S02", [30, 12, 8], [9, 25, 130]),
        ("Protective sleeves", "each", 75, 1.80, 7, "S04", [25, 25, 20], [40, 80, 130]),
        ("Assay kits", "kit", 2, 340, 18, "S04", [40, 45, 25], [15, 30, 130]),
    ]
    materials, lots = [], []
    for index, profile in enumerate(profiles, 1):
        name, unit, demand, cost, lead, supplier, stock_days, expiries = profile
        material_id = f"M{index:03d}"
        materials.append({
            "material_id": material_id, "name": name, "unit": unit,
            "daily_demand": f"{demand:.3f}", "unit_cost": f"{cost:.2f}",
            "lead_time_days": lead, "supplier_id": supplier,
        })
        for lot_index, (stock_day, expiry_offset) in enumerate(zip(stock_days, expiries), 1):
            qty = round(demand * stock_day * rng.uniform(0.92, 1.08), 3)
            if unit in {"each", "vial", "pack", "kit"}:
                qty = round(qty)
            lots.append({
                "lot_id": f"{material_id}-L{lot_index:02d}", "material_id": material_id,
                "qty": f"{qty:.3f}", "unit_cost": f"{cost * rng.uniform(0.97, 1.03):.2f}",
                "quality_status": "Released",
                "expiry_date": (as_of + timedelta(days=expiry_offset)).isoformat(),
            })
        lots.append({
            "lot_id": f"{material_id}-Q01", "material_id": material_id,
            "qty": f"{round(demand * rng.randint(5, 20), 3):.3f}",
            "unit_cost": f"{cost:.2f}", "quality_status": "Quarantine",
            "expiry_date": (as_of + timedelta(days=rng.randint(12, 75))).isoformat(),
        })
        if index % 3 == 0:
            lots.append({
                "lot_id": f"{material_id}-X01", "material_id": material_id,
                "qty": f"{round(demand * rng.randint(2, 6), 3):.3f}",
                "unit_cost": f"{cost:.2f}", "quality_status": "Released",
                "expiry_date": (as_of - timedelta(days=rng.randint(1, 12))).isoformat(),
            })
    write_csv(destination / "suppliers.csv", ["supplier_id", "supplier_name", "category"], suppliers)
    write_csv(destination / "materials.csv", ["material_id", "name", "unit", "daily_demand", "unit_cost", "lead_time_days", "supplier_id"], materials)
    write_csv(destination / "lots.csv", ["lot_id", "material_id", "qty", "unit_cost", "quality_status", "expiry_date"], lots)
    write_csv(destination / "scenario.csv", ["as_of", "seed", "synthetic"], [{"as_of": as_of.isoformat(), "seed": seed, "synthetic": "true"}])
    return {"suppliers": len(suppliers), "materials": len(materials), "lots": len(lots)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--as-of", type=date.fromisoformat, default=DEFAULT_AS_OF)
    args = parser.parse_args()
    counts = generate(args.seed, args.as_of)
    print(f"Generated SYNTHETIC CSVs: {counts}; as of {args.as_of}; seed {args.seed}.")
