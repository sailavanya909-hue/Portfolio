-- Summary reproduces dashboard KPIs without multiplying material-level values
-- by their number of lots. Lot valuation is already rounded to cents by Python.
-- FEFO depletion is a simulation; SQL consumes its explicit projection results.
WITH lot_totals AS (
    SELECT
        COUNT(*) AS lot_count,
        ROUND(SUM(p.inventory_value), 2) AS total_inventory_value,
        ROUND(SUM(CASE WHEN l.quality_status = 'Released'
                       AND l.expiry_date >= sc.as_of THEN p.inventory_value ELSE 0 END), 2)
            AS released_usable_value,
        ROUND(SUM(CASE WHEN l.quality_status = 'Quarantine'
                       THEN p.inventory_value ELSE 0 END), 2) AS quarantined_value,
        ROUND(SUM(CASE WHEN l.quality_status = 'Released'
                       AND l.expiry_date < sc.as_of THEN p.inventory_value ELSE 0 END), 2)
            AS expired_released_value,
        ROUND(SUM(p.expiry_exposed_residual_value), 2) AS expiry_exposed_residual_value
    FROM lots l
    JOIN lot_projection p ON p.lot_id = l.lot_id
    CROSS JOIN scenario sc
), material_totals AS (
    SELECT COUNT(*) AS material_count,
           SUM(CASE WHEN p.lead_time_gap_qty > 0 THEN 1 ELSE 0 END)
               AS materials_below_lead_time_coverage,
           ROUND(SUM(p.replenishment_gap_value), 2) AS replenishment_gap_value
    FROM materials m
    JOIN material_projection p ON p.material_id = m.material_id
)
SELECT * FROM lot_totals CROSS JOIN material_totals;

-- Quantities remain at material grain. Aggregate lots BEFORE joining the
-- one-row-per-material planning metrics; do not SUM daily demand across lots.
WITH by_material AS (
    SELECT l.material_id,
           SUM(p.initial_usable_qty) AS released_usable_qty,
           SUM(CASE WHEN l.quality_status = 'Quarantine' THEN l.qty ELSE 0 END) AS quarantined_qty,
           ROUND(SUM(p.expiry_exposed_residual_value), 2) AS expiry_exposed_residual_value
    FROM lots l
    JOIN lot_projection p ON p.lot_id = l.lot_id
    GROUP BY l.material_id
)
SELECT m.material_id, m.name, m.unit, s.supplier_name, m.daily_demand,
       m.lead_time_days, b.released_usable_qty, b.quarantined_qty,
       p.coverage_days, p.coverage_is_capped, p.lead_time_gap_qty,
       p.replenishment_gap_value, b.expiry_exposed_residual_value
FROM materials m
JOIN suppliers s ON s.supplier_id = m.supplier_id
LEFT JOIN by_material b ON b.material_id = m.material_id
JOIN material_projection p ON p.material_id = m.material_id
ORDER BY p.lead_time_gap_qty > 0 DESC, b.expiry_exposed_residual_value DESC, m.material_id;
