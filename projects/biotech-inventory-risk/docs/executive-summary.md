# Executive summary: simulated inventory review

**Snapshot: 2026-10-09. Horizon: 90 days, through 2027-01-06. All inputs and results are synthetic.**

## Decision

Prioritize materials with a lead-time supply gap for planner review, and investigate released lots with modeled expiry exposure. Total stock alone is insufficient because it includes quarantined and already expired lots.

## Findings

| Measure | Simulated result | Interpretation |
| --- | ---: | --- |
| Inventory purchase-cost value | $523,482.11 | All snapshot lots |
| Released usable purchase-cost value | $423,841.11 | Eligible at the snapshot; future expiry can still constrain supply |
| Quarantined purchase-cost value | $86,929.00 | Visible but excluded from allocation |
| Already expired released purchase-cost value | $12,712.00 | Cannot satisfy demand |
| Released expiry exposure | $106,048.38 | Already expired stock plus modeled residual expiring within the horizon |
| Materials with a lead-time gap | 3 of 12 | At least one day of unmet demand during supplier lead time |
| Estimated replacement cost of lead-time gaps | $37,879.90 | Scenario quantity gap at material replacement cost; no expedite premium |

Measures overlap and must not be added together. Cost exposure is not a booked loss or achieved saving.

## Highest expiry exposure

| Material | Released expiry exposure | FEFO coverage | Supplier lead time |
| --- | ---: | ---: | ---: |
| Assay kits | $39,907.18 | 58 days | 18 days |
| Growth media | $21,151.78 | 29.628 days | 28 days |
| Sterile filters | $20,613.52 | 74.7 days | 35 days |

## Next review actions

1. **Planning and Procurement:** confirm demand and open-order arrival dates for the shortage materials, then evaluate approved replenishment options.
2. **Quality:** review the status and expected release dates of quarantined lots. This model assumes none are released automatically.
3. **Planning and Finance:** review whether earlier consumption, a deferred purchase, or another approved action could reduce future expiry exposure. Already expired stock is not recoverable savings in this model.

The model uses constant daily demand, inclusive expiry dates, and no incoming receipts. The recommendations require validation against production schedules, approved procedures, quality constraints, and actual supplier commitments before business use.
