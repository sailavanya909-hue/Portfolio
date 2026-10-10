# Data dictionary

All records are synthetic. No supplier, product or inventory figure is an actual company record. The default dataset has 4 fictional suppliers, 12 materials and 52 lots, generated with seed 42 for a snapshot on October 9, 2026. The default projection spans 90 calendar days through January 6, 2027, inclusive.

## Raw CSVs

`data/raw/suppliers.csv` has one row per supplier.

| Field | Type | Meaning |
|---|---|---|
| `supplier_id` | Text, primary key | Supplier identifier, for example S01 |
| `supplier_name` | Text | Fictional supplier display name |
| `category` | Text | Illustrative supply category |

`data/raw/materials.csv` has one row per material. Demand and quantities are specific to that material's unit. Two materials that both use kg are still distinct products and cannot substitute for each other.

| Field | Type | Meaning |
|---|---|---|
| `material_id` | Text, primary key | Material identifier, for example M001 |
| `name` | Text | Illustrative raw material or consumable |
| `unit` | Text | g, kg, L, each, vial, pack or kit |
| `daily_demand` | Nonnegative decimal | Constant demand per calendar day in the material's unit |
| `unit_cost` | Nonnegative decimal, USD | Estimated replacement purchase cost per unit; used only to value replenishment gaps |
| `lead_time_days` | Positive integer | Number of daily demand periods before a hypothetical new order arrives |
| `supplier_id` | Text, foreign key | Joins to `suppliers.supplier_id`; one supplier per material in this model |

`data/raw/lots.csv` has one row per lot.

| Field | Type | Meaning |
|---|---|---|
| `lot_id` | Text, primary key | Unique lot identifier |
| `material_id` | Text, foreign key | Joins to `materials.material_id` |
| `qty` | Nonnegative decimal | Snapshot physical quantity, including quarantined and expired stock; each/vial/pack/kit quantities must be whole numbers |
| `unit_cost` | Nonnegative decimal, USD | Lot-specific acquisition cost per material unit; used to value stock and expiry exposure |
| `quality_status` | Enum | `Released` or `Quarantine` |
| `expiry_date` | YYYY-MM-DD | Last day a Released lot can meet simulated demand; expiry occurs after that day's demand |

`data/raw/scenario.csv` has one row with `as_of` (YYYY-MM-DD), `seed` (integer) and `synthetic` (`true`). A generated timestamp is intentionally absent: these files represent a reproducible scenario, not a real-time feed.

## Processed outputs

`data/processed/dashboard.json` contains `meta`, `kpis`, `materials`, `lots`, `expiry_timeline`, `recommendations`, and `methodology`. `site/dashboard.json` is refreshed automatically by the normal analysis command. The executive summary contains the same metadata, KPIs, recommendations and model limitations.

The material and lot CSVs have the same fields as the corresponding JSON arrays. `data/processed/inventory.sqlite3` contains raw supplier/material/lot tables, a scenario row and two explicit projection tables. The SQL examples aggregate raw inventory and join projection results; they do not claim to implement the FEFO simulation in SQL.

| Output field | Meaning |
|---|---|
| `total_inventory_value` / material `total_value` | Snapshot physical quantity × lot acquisition cost across all quality/expiry states |
| `released_usable_qty`, `released_usable_value` | Released stock not expired before the snapshot; this is initial eligibility, not guaranteed future consumption |
| `quarantined_qty`, `quarantined_value` | Quarantine inventory, excluded from demand fulfillment and Released expiry exposure |
| `expired_released_qty`, `expired_released_value` | Released stock expired before the snapshot; no usable inventory |
| `expiry_exposed_residual_value` | Already-expired Released stock plus forecast unconsumed Released quantities that expire within the projection, valued at lot acquisition cost |
| `days_of_supply` | Initial Released eligible quantity ÷ daily demand; ignores subsequent expiry |
| `coverage_days` | Uninterrupted simulated FEFO coverage from the snapshot; includes the fraction served on the first partial day; null for zero demand |
| `coverage_is_capped` | True if coverage reaches the projection horizon; report as “at least” the horizon rather than an exact depletion date |
| `lead_time_gap_qty` | Sum of unmet demand during the material's first `lead_time_days` periods, in that material's unit |
| `replenishment_gap_value` | Material gap × estimated replacement cost, rounded to cents; USD-only portfolio total |
| `materials_below_lead_time_coverage` | Count of materials with positive unmet demand within their lead-time period |
| `initial_usable_qty` | Lot quantity initially available to the model |
| `consumed_qty` | Lot quantity used by demand within the projection |
| `expiry_residual_qty` | Released quantity already expired or remaining when its expiry occurs within the projection; zero for quarantine |
| `remaining_qty` | Lot quantity left at horizon end after modeled consumption/expiry; quarantine remains unchanged |
| `risk` | `Expired`, `Quarantine`, `Expiry exposure` or `Usable` |
| material `status` | `Shortage & expiry risk`, `Shortage risk`, `Expiry risk` or `Healthy` |

Currency values are USD acquisition/replacement costs, not revenue, market prices, realized losses or demonstrated savings. No portfolio quantity KPI adds unlike units or different materials. Zero-demand materials have null days-of-supply/coverage, zero gap, and can still have expiry exposure.

## Reconciliation

For every material and portfolio: total inventory value = initial Released eligible value + quarantined value + already-expired Released value. For every lot: snapshot quantity = consumed quantity + expired residual quantity + remaining quantity. Quarantine expiry is not modeled as Released exposure, so its quantity remains in the quarantine balance.

Lot inventory and expiry values are rounded to cents using Python Decimal's half-even rounding before aggregation. This keeps displayed lot, material and portfolio cost totals consistent. Coverage and quantity outputs are rounded to three decimal places only for presentation; the simulation uses Decimal arithmetic.
