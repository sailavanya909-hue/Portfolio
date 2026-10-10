# User acceptance test plan

## Purpose and execution

Check that a planner can trust the interpretation of the inventory risks and trace the supporting data. These are planned acceptance tests; they should not be described as completed until their outcomes are recorded.

Use small, controlled fixtures with known results. Keep them separate from the generated portfolio scenario. For each test, record the input fixture, settings, actual result, pass/fail status, reviewer, and date. If a case fails, record the defect and rerun it after the change. Expiry is inclusive: released stock can be consumed on its expiry date. Lead-time gaps accumulate unserved demand over the first `lead_time_days`; horizon must be at least the maximum lead time.

## Cases

| ID | Setup and action | Expected result |
| --- | --- | --- |
| UAT-01: FEFO order | Two released lots of the same material have sufficient stock and different future expiry dates. Run allocation with demand below combined quantity. | Consume the earliest expiry lot first; allocation plus remaining stock equals opening quantity for each lot. |
| UAT-02: Quarantine exclusion | One quarantined lot and one released lot share a material. Demand exceeds released stock but is below total stock. | Quarantined stock stays unallocated; shortage remains visible despite the higher total-stock number. |
| UAT-03: Expired released stock | A lot is marked released but expired before the inventory snapshot. | Allocate none of it. Include its remaining quantity at lot acquisition cost in released expiry exposure, with expired status distinguishable from available supply. |
| UAT-04: Expiry boundary | Use released lots expiring just before, exactly on, and just after a forecast consumption date. | The lot expiring before that date is unavailable; the other two remain eligible. No lot is consumed after expiry. |
| UAT-05: Horizon boundary | Lots expire just before, exactly on, and just after the horizon end. | Exposure includes only stock that falls inside the disclosed horizon convention; adjacent dates do not leak into the wrong period. |
| UAT-06: Zero demand | Set forecast demand to zero while released stock expires during the horizon. | No allocation or division error; coverage/days of supply are undefined, lead-time gap is zero, and unused released expiring quantity/cost remain visible. |
| UAT-07: No inventory | A valid material has positive demand and no inventory lots. | Show no eligible supply and the corresponding unfulfilled demand. |
| UAT-08: Lead-time shortage | Released stock covers less demand than is required before the replenishment lead time. | Flag the material and show the modeled gap. Moving the depletion date across the lead-time boundary changes the result consistently. |
| UAT-09: Tied expiry dates | Two otherwise eligible lots have identical expiry dates. Run twice. | Consume in lot-ID order; output is identical on both runs. |
| UAT-10: Missing required values | Remove a required material ID, lot ID, date, status, quantity, cost, or demand field. | Reject input with a useful field/record error; do not silently assign zero or omit the lot. |
| UAT-11: Duplicate identifiers | Repeat a material or lot key with identical or conflicting data. | Reject duplicate keys before analysis; no double counting. |
| UAT-12: Invalid records | Add an unknown supplier/material reference, unrecognized lot status, malformed date, negative quantity/cost/demand, nonpositive lead time, nonnumeric value, or horizon below maximum lead time. | Reject the invalid input/settings and explain the reason. No partial successful report is presented as complete. |
| UAT-13: Conservation and valuation | Use a small known fixture, calculate allocation and remaining quantities by hand, and multiply exposed stock by the stated cost. | Lot and material results reconcile to the manual calculation, subject only to disclosed rounding. |
| UAT-14: Dashboard reconciliation | Generate results, open the dashboard, and inspect its KPIs and a material detail. | Values agree with the output from the same run; dates/settings and synthetic-data labels are visible. |
| UAT-15: Reproducible run | Run generation with the same seed/settings and analyze the same inputs twice. | Input and analytical output are reproducible; ordering is stable. |
| UAT-16: Different cost bases | Give a material a replacement cost of 8 and an expiring lot an acquisition cost of 5. Create 3 units of lead-time gap and 2 units of released expiry exposure. | The gap estimate is 24 and expiry exposure is 10 in the modeled currency; valuation does not mix the two cost bases. |
| UAT-17: Incompatible units | Include materials measured in kilograms and liters. Review totals and filters. | Quantity summaries remain material-specific; no combined kg-plus-liter total appears. Monetary exposure may be totaled. |

## Acceptance record

| Test ID | Fixture / settings | Actual result | Status | Reviewer / date |
| --- | --- | --- | --- | --- |
| _Complete during review_ | | | Not run | |

Use **Pass**, **Fail**, or **Not run**. All applicable cases must pass before claiming UAT completion. An excluded case needs a recorded scope reason. Confirm that automated tests cover the essential calculation and validation cases; a manual dashboard review is still needed for readability and interpretation.
