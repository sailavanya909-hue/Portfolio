-- Rebuilt by analyze.py. Raw tables and FEFO projection outputs are separate.
PRAGMA foreign_keys = ON;
DROP TABLE IF EXISTS lot_projection;
DROP TABLE IF EXISTS material_projection;
DROP TABLE IF EXISTS lots;
DROP TABLE IF EXISTS materials;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS scenario;
CREATE TABLE suppliers (
    supplier_id TEXT PRIMARY KEY, supplier_name TEXT NOT NULL, category TEXT
);
CREATE TABLE materials (
    material_id TEXT PRIMARY KEY, name TEXT NOT NULL, unit TEXT NOT NULL,
    daily_demand REAL NOT NULL CHECK (daily_demand >= 0),
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days > 0),
    supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id)
);
CREATE TABLE lots (
    lot_id TEXT PRIMARY KEY, material_id TEXT NOT NULL REFERENCES materials(material_id),
    qty REAL NOT NULL CHECK (qty >= 0), unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
    quality_status TEXT NOT NULL CHECK (quality_status IN ('Released', 'Quarantine')),
    expiry_date TEXT NOT NULL
);
CREATE TABLE scenario (as_of TEXT NOT NULL, horizon_days INTEGER NOT NULL);
CREATE TABLE lot_projection (
    lot_id TEXT PRIMARY KEY REFERENCES lots(lot_id), inventory_value REAL NOT NULL,
    initial_usable_qty REAL NOT NULL, consumed_qty REAL NOT NULL,
    expiry_residual_qty REAL NOT NULL, expiry_exposed_residual_value REAL NOT NULL,
    remaining_qty REAL NOT NULL
);
CREATE TABLE material_projection (
    material_id TEXT PRIMARY KEY REFERENCES materials(material_id), coverage_days REAL,
    coverage_is_capped INTEGER NOT NULL, lead_time_gap_qty REAL NOT NULL,
    replenishment_gap_value REAL NOT NULL
);
