# Methodology and limits

This is a reproducible business-analysis portfolio case using synthetic biotech materials. Default parameters are seed 42, snapshot October 9, 2026 and a 90-day projection ending January 6, 2027. Run the scripts from the project root with Python 3.9 or newer; no packages or network are needed.

```text
python3 src/generate_data.py
python3 src/analyze.py
python3 src/query_sql.py
python3 -m unittest discover -s tests -v
```

The generator deliberately creates materials with low stock, ample stock, early expiries, quarantine and already-expired inventory. These are constructed operational scenarios, not statistically representative biotech inventory. Whole-count consumables are generated as integers; mass and volume quantities can have decimals.

## How the projection works

1. Validate unique supplier/material/lot identifiers, relationships, quality states, ISO dates, quantities, costs, demand and lead times. Reject invalid states, negative/nonfinite numbers and fractional quantities for whole-count units. Every lead time must fit inside the projection horizon; a shorter horizon is rejected rather than understating the gap.
2. Classify starting inventory. Only Released lots with expiry on or after the snapshot can meet demand. Released lots already expired are immediately assigned to expired residual quantity. Quarantine never becomes Released in this scenario.
3. For each material independently, order lots by expiry, then lot identifier. Starting on the snapshot, consume daily demand from eligible lots in this FEFO order. Expiry dates are inclusive: a lot can be consumed on its expiry date, then any residual expires at the day's close.
4. Record actual served and unmet demand every day. Unmet demand is not backlogged or fulfilled later. Record uninterrupted coverage through the first partially served day. If no shortage occurs within the horizon, report coverage as at least the horizon; this is not a known future depletion date.
5. Sum unmet demand through the material's supplier lead-time period. A hypothetical order placed at the snapshot arrives at the start of the day after that period. The quantity gap is specific to that material; its currency value uses the material's estimated replacement cost.
6. Value inventory and residual expiry exposure using each lot's acquisition cost. Exposure includes already-expired Released stock and residual Released stock expiring within the horizon. Lots expiring after the horizon contribute no expiry exposure in this run. Quarantine is reported separately, including quarantined stock whose expiry passes during the run.

The model has no incoming purchases, production receipts, substitutions, scrap adjustments or automatic quality releases. Demand is constant on calendar days, including weekends. Supplier lead times are fixed. There is no safety stock policy, service-level target or storage/capacity constraint. Estimated replacement cost is not a supplier quote and does not include freight, expediting, disposal or holding costs.

## Interpreting the business measures

`days_of_supply` is a quick starting-stock ratio. `coverage_days` accounts for later expiry and can therefore be shorter. This difference is central to the case: abundant physical inventory can coexist with an operational gap when lots expire or remain in quarantine.

The expiry measure describes purchase cost exposed under the scenario. It does not establish realized loss or achievable savings. Already-expired Released stock is part of that exposure and cannot be rescued through future FEFO. Any proposed benefit requires a second scenario with feasible demand changes, supplier dates, and quality approvals. Expiry and gap measures can both apply to one material and must not be summed as a promised financial benefit.

Portfolio quantities are never summed across materials. Even matching units do not imply interchangeability. Portfolio currency totals are valid here because every cost is denominated in USD. Rounding happens at the lot cost line to cents before aggregation; quantity/coverage display rounding is separate from model arithmetic.

## Parameters and reproducibility

`generate_data.py --seed 7 --as-of 2026-10-09` creates a different synthetic scenario. `analyze.py --horizon 120` extends its projection. The analyzer ordinarily reads the snapshot date and seed from `scenario.csv`; an optional `--as-of YYYY-MM-DD` re-evaluates the same physical quantities at a different starting date. That override is a scenario stress test: it does not pretend to reconstruct intervening historical consumption. Regenerate inputs for a fully shifted synthetic snapshot.

The analysis refreshes dashboard JSON, risk-detail CSVs, executive-summary JSON, SQLite database and the static site's dashboard JSON. Custom output directories used by unit tests do not overwrite the public site. Deterministic content intentionally contains no fabricated generation timestamp.

## SQL and checks

The Python FEFO model is the depletion engine. SQLite stores its lot/material projections separately from raw tables. `sql/analysis.sql` reproduces the displayed summary using one-to-one lot/projection joins and separately aggregated material metrics; it aggregates lots before joining material demand to avoid multiplication by lot count. `python3 src/query_sql.py` opens the generated database read-only and runs both example queries.

Tests exercise inclusive expiry, expired/quarantine exclusion, FEFO ordering and ties, fractional coverage, zero demand, horizon boundaries, distinct acquisition/replacement costs, per-lot conservation, valuation reconciliation, discrete units, invalid inputs, seeded reproducibility and agreement between SQLite and dashboard KPIs. These checks validate the stated model, not an operational planning policy for a real manufacturer.
