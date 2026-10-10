#!/usr/bin/env python3
"""Analyze synthetic inventory using discrete daily FEFO depletion; stdlib only."""
import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZERO = Decimal("0")


def nonnegative(value, name):
    try:
        number = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{name} must be a finite nonnegative number") from exc
    if not number.is_finite() or number < ZERO:
        raise ValueError(f"{name} must be a finite nonnegative number")
    return number


def iso_date(value):
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError(f"Date must use YYYY-MM-DD: {value}")
    return parsed


def numeric(value, places=3):
    return float(round(value, places))


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def unique(rows, key):
    result = {}
    for row in rows:
        value = row[key]
        if not value or value in result:
            raise ValueError(f"Missing or duplicate {key}: {value!r}")
        result[value] = row
    return result


def simulate_fefo(lots, daily_demand, as_of, horizon_days):
    """Return exact Decimal balances and daily demand fulfillment per material.

    Expiry dates are usable through that day's close. No incoming supply or
    quarantine releases are assumed. A shortage is lost daily demand, not a
    backlog that consumes later inventory. Input order cannot change FEFO.
    """
    if horizon_days <= 0:
        raise ValueError("horizon_days must be positive")
    demand = nonnegative(daily_demand, "daily_demand")
    unique(lots, "lot_id")
    balances = []
    for lot in lots:
        qty = nonnegative(lot["qty"], "qty")
        cost = nonnegative(lot["unit_cost"], "unit_cost")
        expiry = iso_date(lot["expiry_date"])
        status = lot["quality_status"]
        if status not in {"Released", "Quarantine"}:
            raise ValueError(f"Invalid quality_status: {status}")
        eligible = status == "Released" and expiry >= as_of
        expired = status == "Released" and expiry < as_of
        balances.append({
            **lot, "qty": qty, "unit_cost": cost, "expiry": expiry,
            "initial_usable_qty": qty if eligible else ZERO,
            "consumed_qty": ZERO, "expiry_residual_qty": qty if expired else ZERO,
            "remaining_qty": ZERO if expired else qty,
        })
    balances.sort(key=lambda item: (item["expiry"], item["lot_id"]))
    days = []
    coverage = None if demand == ZERO else Decimal(horizon_days)
    capped = demand != ZERO
    for offset in range(horizon_days):
        current = as_of + timedelta(days=offset)
        unserved = demand
        for lot in balances:
            if lot["quality_status"] != "Released" or lot["expiry"] < current:
                continue
            consumed = min(lot["remaining_qty"], unserved)
            lot["remaining_qty"] -= consumed
            lot["consumed_qty"] += consumed
            unserved -= consumed
            if unserved == ZERO:
                break
        served = demand - unserved
        days.append({"date": current.isoformat(), "served_qty": served, "unserved_qty": unserved})
        if unserved > ZERO and capped:
            coverage = Decimal(offset) + served / demand
            capped = False
        # Anything remaining expires after today's demand has been consumed.
        for lot in balances:
            if lot["quality_status"] == "Released" and lot["expiry"] == current:
                lot["expiry_residual_qty"] += lot["remaining_qty"]
                lot["remaining_qty"] = ZERO
    for lot in balances:
        assert lot["qty"] == lot["consumed_qty"] + lot["expiry_residual_qty"] + lot["remaining_qty"]
    return {"lots": balances, "days": days, "coverage_days": coverage, "coverage_is_capped": capped}


METHODOLOGY = [
    "All materials, suppliers, lots and results are synthetic; the data-generation seed appears in metadata.",
    "Daily FEFO uses Released lots only, ordered by expiry date then lot ID; expiry is at the end of the expiry date.",
    "Constant material-specific daily demand; no receipts, automatic quality releases, substitution or safety stock.",
    "Expiry exposure is residual Released lot purchase cost that is already expired or expires within the selected projection horizon; quarantine is excluded.",
    "Lead-time gaps are unmet demand before a hypothetical order arriving at the start of day lead_time_days + 1; currency totals use each material's replacement cost.",
    "Quantities are meaningful only within each material's stated unit; portfolio totals aggregate costs in USD, never mixed-unit quantities.",
    "Projected exposure and replacement cost are scenario measures, not realized savings, confirmed losses or purchasing instructions.",
]


def analyze_rows(suppliers, materials, lots, as_of, horizon_days=90, seed=42):
    supplier_map = unique(suppliers, "supplier_id")
    for supplier in suppliers:
        if not supplier["supplier_name"].strip():
            raise ValueError(f"Supplier {supplier['supplier_id']} needs a supplier_name")
    material_map = unique(materials, "material_id")
    unique(lots, "lot_id")
    grouped = defaultdict(list)
    for lot in lots:
        if lot["material_id"] not in material_map:
            raise ValueError(f"Unknown lot material: {lot['material_id']}")
        grouped[lot["material_id"]].append(lot)
    material_result, lot_result, recommendations = [], [], []
    timeline = defaultdict(lambda: ZERO)
    for material_id, material in sorted(material_map.items()):
        if material["supplier_id"] not in supplier_map:
            raise ValueError(f"Unknown material supplier: {material['supplier_id']}")
        if not material["unit"].strip() or not material["name"].strip():
            raise ValueError(f"Material {material_id} needs a name and unit")
        if material["unit"] in {"each", "vial", "pack", "kit"}:
            for lot in grouped[material_id]:
                quantity = nonnegative(lot["qty"], "qty")
                if quantity != quantity.to_integral_value():
                    raise ValueError(f"Lot {lot['lot_id']} requires whole-number quantities for unit {material['unit']}")
        lead = int(material["lead_time_days"])
        if str(lead) != str(material["lead_time_days"]) or lead <= 0:
            raise ValueError("lead_time_days must be a positive integer")
        if horizon_days < lead:
            raise ValueError("Horizon must include every material's lead time")
        demand = nonnegative(material["daily_demand"], "daily_demand")
        replacement_cost = nonnegative(material["unit_cost"], "unit_cost")
        supplier = supplier_map[material["supplier_id"]]
        result = simulate_fefo(grouped[material_id], demand, as_of, horizon_days)
        total_qty = sum((lot["qty"] for lot in result["lots"]), ZERO)
        usable_qty = sum((lot["initial_usable_qty"] for lot in result["lots"]), ZERO)
        quarantine_qty = sum((lot["qty"] for lot in result["lots"] if lot["quality_status"] == "Quarantine"), ZERO)
        expired_qty = sum((lot["qty"] for lot in result["lots"] if lot["quality_status"] == "Released" and lot["expiry"] < as_of), ZERO)
        total_value = sum((round(lot["qty"] * lot["unit_cost"], 2) for lot in result["lots"]), ZERO)
        usable_value = sum((round(lot["initial_usable_qty"] * lot["unit_cost"], 2) for lot in result["lots"]), ZERO)
        quarantine_value = sum((round(lot["qty"] * lot["unit_cost"], 2) for lot in result["lots"] if lot["quality_status"] == "Quarantine"), ZERO)
        expired_value = sum((round(lot["qty"] * lot["unit_cost"], 2) for lot in result["lots"] if lot["quality_status"] == "Released" and lot["expiry"] < as_of), ZERO)
        assert total_value == usable_value + quarantine_value + expired_value
        gap = sum((day["unserved_qty"] for day in result["days"][:lead]), ZERO)
        gap_value = gap * replacement_cost
        exposure = sum((round(lot["expiry_residual_qty"] * lot["unit_cost"], 2) for lot in result["lots"]), ZERO)
        shortage = gap > ZERO
        status = "Shortage & expiry risk" if shortage and exposure > ZERO else "Shortage risk" if shortage else "Expiry risk" if exposure > ZERO else "Healthy"
        material_result.append({
            "material_id": material_id, "name": material["name"], "unit": material["unit"],
            "daily_demand": numeric(demand), "unit_cost": numeric(replacement_cost, 2),
            "lead_time_days": lead, "supplier_id": material["supplier_id"], "supplier_name": supplier["supplier_name"],
            "total_qty": numeric(total_qty), "released_usable_qty": numeric(usable_qty),
            "quarantined_qty": numeric(quarantine_qty), "expired_released_qty": numeric(expired_qty),
            "total_value": numeric(total_value, 2), "released_usable_value": numeric(usable_value, 2),
            "quarantined_value": numeric(quarantine_value, 2), "expired_released_value": numeric(expired_value, 2),
            "expiry_exposed_residual_value": numeric(exposure, 2),
            "coverage_days": numeric(result["coverage_days"]) if result["coverage_days"] is not None else None,
            "coverage_is_capped": result["coverage_is_capped"],
            "days_of_supply": numeric(usable_qty / demand) if demand else None,
            "lead_time_gap_qty": numeric(gap), "replenishment_gap_value": numeric(gap_value, 2), "status": status,
        })
        for lot in result["lots"]:
            residual_value = round(lot["expiry_residual_qty"] * lot["unit_cost"], 2)
            risk = "Quarantine" if lot["quality_status"] == "Quarantine" else "Expired" if lot["expiry"] < as_of else "Expiry exposure" if residual_value > ZERO else "Usable"
            row = {
                "lot_id": lot["lot_id"], "material_id": material_id, "material_name": material["name"],
                "unit": material["unit"], "supplier_id": material["supplier_id"], "supplier_name": supplier["supplier_name"],
                "quality_status": lot["quality_status"], "expiry_date": lot["expiry_date"],
                "qty": numeric(lot["qty"]), "unit_cost": numeric(lot["unit_cost"], 2),
                "inventory_value": numeric(lot["qty"] * lot["unit_cost"], 2),
                "initial_usable_qty": numeric(lot["initial_usable_qty"]), "consumed_qty": numeric(lot["consumed_qty"]),
                "expiry_residual_qty": numeric(lot["expiry_residual_qty"]),
                "expiry_exposed_residual_value": numeric(residual_value, 2),
                "remaining_qty": numeric(lot["remaining_qty"]), "risk": risk,
            }
            lot_result.append(row)
            if residual_value:
                timeline[lot["expiry_date"]] += residual_value
        if shortage:
            recommendations.append({"priority": "High", "material_id": material_id, "action": "Review replenishment options and quality-release schedule", "reason": f"Projected lead-time gap: {numeric(gap):g} {material['unit']}; {numeric(result['coverage_days']):g} days of uninterrupted coverage versus {lead} lead-time days."})
        if exposure:
            recommendations.append({"priority": "High" if shortage else "Medium", "material_id": material_id, "action": "Review expiring lots with planning and quality teams", "reason": f"USD {numeric(exposure, 2):,.2f} of Released lot purchase cost is already expired or projected to remain at expiry within the horizon; quantify feasible demand changes before claiming savings."})
    # The published KPI totals equal the displayed lot/material cents exactly.
    def total(rows, key):
        return numeric(sum((Decimal(str(row[key])) for row in rows), ZERO), 2)
    kpis = {
        "total_inventory_value": total(lot_result, "inventory_value"),
        "released_usable_value": total(material_result, "released_usable_value"),
        "quarantined_value": total(material_result, "quarantined_value"),
        "expired_released_value": total(material_result, "expired_released_value"),
        "expiry_exposed_residual_value": total(lot_result, "expiry_exposed_residual_value"),
        "materials_below_lead_time_coverage": sum(row["lead_time_gap_qty"] > 0 for row in material_result),
        "replenishment_gap_value": total(material_result, "replenishment_gap_value"),
        "material_count": len(material_result), "lot_count": len(lot_result),
    }
    return {
        "meta": {"as_of": as_of.isoformat(), "horizon_days": horizon_days,
                 "horizon_end": (as_of + timedelta(days=horizon_days - 1)).isoformat(),
                 "currency": "USD", "synthetic": True, "seed": seed,
                 "description": "Synthetic biotech raw-material inventory scenario; no company or patient data."},
        "kpis": kpis, "materials": material_result, "lots": lot_result,
        "expiry_timeline": [{"date": key, "residual_value": numeric(value, 2)} for key, value in sorted(timeline.items())],
        "recommendations": recommendations, "methodology": METHODOLOGY,
    }


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export_sqlite(path, suppliers, materials, lots, dashboard):
    """Store raw inputs and model outputs separately for transparent SQL review."""
    with sqlite3.connect(str(path)) as connection:
        connection.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
        tables = {
            "suppliers": suppliers, "materials": materials, "lots": lots,
            "scenario": [{"as_of": dashboard["meta"]["as_of"], "horizon_days": dashboard["meta"]["horizon_days"]}],
            "lot_projection": [{key: row[key] for key in ("lot_id", "inventory_value", "initial_usable_qty", "consumed_qty", "expiry_residual_qty", "expiry_exposed_residual_value", "remaining_qty")} for row in dashboard["lots"]],
            "material_projection": [{key: row[key] for key in ("material_id", "coverage_days", "coverage_is_capped", "lead_time_gap_qty", "replenishment_gap_value")} for row in dashboard["materials"]],
        }
        for table, rows in tables.items():
            if not rows:
                continue
            columns = list(rows[0])
            placeholders = ",".join("?" for _ in columns)
            statement = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
            connection.executemany(statement, [[row[column] for column in columns] for row in rows])


def run(as_of=None, horizon_days=90, raw_dir=None, output_dir=None):
    raw = Path(raw_dir) if raw_dir else ROOT / "data" / "raw"
    output = Path(output_dir) if output_dir else ROOT / "data" / "processed"
    scenario = read_csv(raw / "scenario.csv")[0]
    if scenario.get("synthetic") != "true":
        raise ValueError("This portfolio dataset must be explicitly labeled synthetic")
    effective_date = as_of or iso_date(scenario["as_of"])
    suppliers, materials, lots = read_csv(raw / "suppliers.csv"), read_csv(raw / "materials.csv"), read_csv(raw / "lots.csv")
    dashboard = analyze_rows(suppliers, materials, lots, effective_date, horizon_days, int(scenario["seed"]))
    output.mkdir(parents=True, exist_ok=True)
    (output / "dashboard.json").write_text(json.dumps(dashboard, indent=2) + "\n", encoding="utf-8")
    write_csv(output / "lot-risk-detail.csv", dashboard["lots"])
    write_csv(output / "material-risk-detail.csv", dashboard["materials"])
    executive = {"meta": dashboard["meta"], "kpis": dashboard["kpis"],
                 "recommendations": dashboard["recommendations"], "limitations": dashboard["methodology"]}
    (output / "executive-summary.json").write_text(json.dumps(executive, indent=2) + "\n", encoding="utf-8")
    export_sqlite(output / "inventory.sqlite3", suppliers, materials, lots, dashboard)
    if output_dir is None:
        site = ROOT / "site"
        site.mkdir(parents=True, exist_ok=True)
        (site / "dashboard.json").write_text(json.dumps(dashboard, indent=2) + "\n", encoding="utf-8")
    return dashboard


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=date.fromisoformat, default=None)
    parser.add_argument("--horizon", type=int, default=90)
    args = parser.parse_args()
    report = run(args.as_of, args.horizon)
    print(json.dumps(report["kpis"], indent=2))
