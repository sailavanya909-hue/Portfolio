import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from analyze import analyze_rows, run, simulate_fefo
from generate_data import generate
from query_sql import query_results
from analyze import read_csv

AS_OF = date(2026, 10, 9)


def lot(identifier, qty, expiry, status="Released", cost="2.00", material_id="M1"):
    return {"lot_id": identifier, "material_id": material_id, "qty": str(qty),
            "unit_cost": cost, "quality_status": status, "expiry_date": expiry}


class FefoTests(unittest.TestCase):
    def test_expiry_day_is_usable_and_only_residual_expires(self):
        result = simulate_fefo([lot("A", 25, "2026-10-09")], 10, AS_OF, 3)
        balance = result["lots"][0]
        self.assertEqual(balance["consumed_qty"], Decimal(10))
        self.assertEqual(balance["expiry_residual_qty"], Decimal(15))
        self.assertEqual(balance["remaining_qty"], Decimal(0))
        self.assertEqual(result["coverage_days"], Decimal(1))
        self.assertEqual(sum(day["unserved_qty"] for day in result["days"]), Decimal(20))

    def test_fefo_sorting_ignores_input_order_and_uses_lot_id_for_ties(self):
        source = [lot("Z", 10, "2026-11-01"), lot("B", 10, "2026-10-10"), lot("A", 10, "2026-10-10")]
        balances = {row["lot_id"]: row for row in simulate_fefo(source, 15, AS_OF, 1)["lots"]}
        self.assertEqual(balances["A"]["consumed_qty"], Decimal(10))
        self.assertEqual(balances["B"]["consumed_qty"], Decimal(5))
        self.assertEqual(balances["Z"]["consumed_qty"], Decimal(0))

    def test_expired_and_quarantined_lots_never_meet_demand(self):
        source = [lot("X", 100, "2026-10-08"), lot("Q", 100, "2026-10-12", "Quarantine"), lot("R", 5, "2026-10-20")]
        result = simulate_fefo(source, 10, AS_OF, 2)
        balances = {row["lot_id"]: row for row in result["lots"]}
        self.assertEqual(balances["X"]["initial_usable_qty"], Decimal(0))
        self.assertEqual(balances["X"]["expiry_residual_qty"], Decimal(100))
        self.assertEqual(balances["Q"]["consumed_qty"], Decimal(0))
        self.assertEqual(balances["Q"]["expiry_residual_qty"], Decimal(0))
        self.assertEqual(balances["Q"]["remaining_qty"], Decimal(100))
        self.assertEqual(result["coverage_days"], Decimal("0.5"))
        self.assertEqual(sum(day["unserved_qty"] for day in result["days"]), Decimal(15))

    def test_expiry_beyond_horizon_is_not_counted_as_exposure(self):
        balance = simulate_fefo([lot("R", 100, "2026-10-12")], 10, AS_OF, 3)["lots"][0]
        self.assertEqual(balance["consumed_qty"], Decimal(30))
        self.assertEqual(balance["remaining_qty"], Decimal(70))
        self.assertEqual(balance["expiry_residual_qty"], Decimal(0))

    def test_zero_demand_still_exposes_expiring_stock_without_fake_shortage(self):
        result = simulate_fefo([lot("R", 4, "2026-10-09")], 0, AS_OF, 2)
        self.assertIsNone(result["coverage_days"])
        self.assertEqual(result["lots"][0]["expiry_residual_qty"], Decimal(4))
        self.assertEqual(sum(day["unserved_qty"] for day in result["days"]), Decimal(0))

    def test_invalid_input_is_rejected(self):
        for bad in [lot("A", -1, "2026-10-10"), lot("A", "NaN", "2026-10-10"),
                    lot("A", 1, "2026-10-10", "Unknown")]:
            with self.assertRaises(ValueError):
                simulate_fefo([bad], 1, AS_OF, 3)
        with self.assertRaises(ValueError):
            simulate_fefo([lot("A", 1, "2026-10-10"), lot("A", 2, "2026-10-11")], 1, AS_OF, 3)


class ReportTests(unittest.TestCase):
    def test_costs_and_material_units_reconcile_without_fanout(self):
        suppliers = [{"supplier_id": "S1", "supplier_name": "Test Supplier"}]
        materials = [{"material_id": "M1", "name": "Test", "unit": "kg", "daily_demand": "10", "unit_cost": "7", "lead_time_days": "2", "supplier_id": "S1"}]
        lots = [lot("X", 4, "2026-10-08", cost="3"), lot("Q", 20, "2026-10-12", "Quarantine", "5"), lot("R", 15, "2026-10-09", cost="2")]
        report = analyze_rows(suppliers, materials, lots, AS_OF, 3)
        metrics = report["kpis"]
        self.assertEqual(metrics["total_inventory_value"], 142.0)
        self.assertEqual(metrics["released_usable_value"], 30.0)
        self.assertEqual(metrics["quarantined_value"], 100.0)
        self.assertEqual(metrics["expired_released_value"], 12.0)
        self.assertEqual(metrics["expiry_exposed_residual_value"], 22.0)
        self.assertEqual(metrics["replenishment_gap_value"], 70.0)
        self.assertEqual(report["materials"][0]["lead_time_gap_qty"], 10.0)
        self.assertEqual(metrics["materials_below_lead_time_coverage"], 1)
        self.assertEqual(report["materials"][0]["days_of_supply"], 1.5)
        self.assertEqual(report["materials"][0]["coverage_days"], 1.0)
        self.assertNotIn("total_qty", metrics)

    def test_unknown_material_and_short_horizon_are_rejected(self):
        suppliers = [{"supplier_id": "S1", "supplier_name": "Test"}]
        materials = [{"material_id": "M1", "name": "Test", "unit": "each", "daily_demand": "1", "unit_cost": "2", "lead_time_days": "4", "supplier_id": "S1"}]
        with self.assertRaises(ValueError):
            analyze_rows(suppliers, materials, [lot("R", 1, "2026-10-10", material_id="missing")], AS_OF, 5)
        with self.assertRaises(ValueError):
            analyze_rows(suppliers, materials, [], AS_OF, 3)

    def test_seed_reproducibility_end_to_end_and_balances(self):
        with tempfile.TemporaryDirectory() as location:
            raw, processed = Path(location) / "raw", Path(location) / "processed"
            generate(42, AS_OF, raw)
            first = run(raw_dir=raw, output_dir=processed)
            first_bytes = (processed / "dashboard.json").read_bytes()
            generate(42, AS_OF, raw)
            second = run(raw_dir=raw, output_dir=processed)
            self.assertEqual(first, second)
            self.assertEqual(first_bytes, (processed / "dashboard.json").read_bytes())
            for row in first["lots"]:
                self.assertAlmostEqual(row["qty"], row["consumed_qty"] + row["expiry_residual_qty"] + row["remaining_qty"], places=3)
            metrics = first["kpis"]
            self.assertAlmostEqual(metrics["total_inventory_value"], metrics["released_usable_value"] + metrics["quarantined_value"] + metrics["expired_released_value"], places=2)
            self.assertEqual(metrics["lot_count"], 52)
            self.assertEqual(metrics["material_count"], 12)
            material_units = {row["material_id"]: row["unit"] for row in read_csv(raw / "materials.csv")}
            for row in read_csv(raw / "lots.csv"):
                if material_units[row["material_id"]] in {"each", "vial", "pack", "kit"}:
                    quantity = Decimal(row["qty"])
                    self.assertEqual(quantity, quantity.to_integral_value())
            summary = query_results(processed / "inventory.sqlite3")[0][0]
            for key, value in metrics.items():
                self.assertEqual(summary[key], value, key)


if __name__ == "__main__":
    unittest.main()
