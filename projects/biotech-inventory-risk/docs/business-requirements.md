# Business requirements

## Objective and stakeholders

Help a supply planner review raw-material availability when stock is held in lots with different expiry dates and release statuses. Help Finance understand the modeled value of stock exposed to expiry, and give Quality visibility into planning eligibility.

The scenario is a fictional biotech manufacturer. All materials, suppliers, lots, costs, and demand are generated for this portfolio. The requirements are a project specification; they have not been approved by an actual employer or regulated manufacturing organization.

## Scope

In scope: one inventory snapshot, material and lot records, constant daily forecast demand, material lead times, FEFO allocation, quarantine and expiry exclusions, shortage analysis, estimated expiry exposure, and a static review dashboard.

Sources are generated CSV files in `data/raw/`: `suppliers.csv`, `materials.csv`, and `lots.csv`. Material records contain demand, units, replacement cost, and lead time. Lot records contain quantity, release status, expiry, and acquisition cost. Defaults are an October 9, 2026 snapshot and a 90-day horizon through January 6, 2027.

Out of scope: purchase-order execution, real-time ERP integration, automated quality release, validated GMP workflows, product batch genealogy, production scheduling, and claims of actual cost savings.

## Decision rules

Use a common snapshot date and consistent material units. Forecast and inventory quantities must use the same unit for a given material. Lots have either Released or Quarantine status. A released lot is usable through its expiry date and unavailable afterward. Quarantined lots never auto-release. FEFO means earliest expiry first, with lot ID as the deterministic tie-breaker.

The forecast is constant daily demand. The model simulates allocation without receipts, backorders, substitution, or safety stock. The lead-time gap is cumulative unserved demand during the first `lead_time_days`, valued at the material replacement cost. Released expiry exposure includes stock already expired at the snapshot and released residual stock expiring within the horizon, valued at lot acquisition cost; quarantine is excluded. Coverage is uninterrupted simulated coverage, including a fractional first shortage day and capped at the horizon. Simple days of supply divides usable starting quantity by daily demand and ignores future expiry. Both coverage measures are undefined for zero demand.

The implementation must disclose these conventions and any rounding. Missing values must not silently become favorable risk outcomes. Horizon must cover every material's lead time.

## Functional requirements and acceptance criteria

| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| BR-01 | Load and validate supplier, material, and inventory inputs. | Inputs have unique required keys, valid foreign keys, recognized statuses, valid ISO dates, nonnegative quantity/demand/cost, and positive lead time. Invalid records stop analysis with a useful error; they are not silently dropped. A horizon shorter than the maximum lead time is rejected. |
| BR-02 | Distinguish total stock from planning-eligible stock. | Quarantined or otherwise ineligible lots cannot satisfy forecast demand. Totals show their quantities separately so excluded stock is visible. |
| BR-03 | Allocate released stock by FEFO. | The earliest-expiring eligible lot is consumed first. No lot allocation exceeds its available quantity, and no inventory is consumed after the model's expiry boundary. |
| BR-04 | Identify shortage risk before supply can be replenished. | Material results show cumulative unserved demand during the first `lead_time_days` and its replacement-cost estimate. No receipts are assumed. Boundary tests cover the lead-time window. |
| BR-05 | Quantify released inventory exposed to expiry. | Already expired released lots and released residual stock expiring within the horizon are valued at lot acquisition cost. Quarantine is excluded. Results are labeled exposure, rather than realized waste or savings. |
| BR-06 | Handle inactive or zero-demand materials. | Zero demand does not cause a division error or display a fabricated finite coverage value. Expiry exposure can still be reported for stock that remains unused. |
| BR-07 | Provide an actionable dashboard. | Users can identify material risks, inspect supporting lot information, and see snapshot, horizon, units, eligibility rules, and value assumptions. |
| BR-08 | Make the analysis reproducible. | The same input data and settings yield the same output. Published results can be regenerated from repository instructions. |
| BR-09 | Keep analytical results internally consistent. | Opening quantity equals allocated plus remaining quantity for each lot. Material summaries reconcile to lot-level calculations. SQL checks use compatible definitions and input data. |
| BR-10 | Label the provenance and limits of the work. | README and dashboard state that data is synthetic and figures are modeled. No unsupported GMP certification, actual company results, SAP experience, or savings claims appear. |

## Proposed user workflow

1. Planner reviews materials with near-term shortage risk and inspects released versus quarantined stock.
2. Planner checks the earliest expiry lots and forecast consumption assumptions.
3. Quality reviews whether a status or release-timing assumption needs correction; the dashboard cannot release a lot.
4. Finance reviews the cost value of potentially unused expiring stock.
5. The team records a proposed action, owner, and follow-up question. Any operational action requires separate business approval.

## Acceptance evidence

Keep automated test results, the completed UAT record, reconciliation outputs, and a dashboard screenshot for the same input run. Acceptance requires BR-01 through BR-10 to pass or any remaining gap to be clearly recorded. Running a test suite alone is not proof that a planner has approved the solution.

## Assumptions and limitations

Generated demand is a planning assumption, not actual customer orders. Acquisition and replacement costs are separate analytical valuation bases. Quantities remain in each material's unit and are not summed across incompatible units. Missing orders, yield loss, demand variability, batch-size constraints, delayed quality release, and supplier capacity can change a real decision. This project is educational and requires further validation before operational use.
