# Executed verification

Verified on October 9, 2026 with Python 3.9.6 using the published seed 42 scenario and a 90-day horizon. All source data is synthetic.

| Check | Result |
| --- | --- |
| Generate and analyze from source | Passed: 4 suppliers, 12 materials, 52 lots |
| Automated calculation suite | Passed: 9 tests |
| SQLite summary versus dashboard JSON | Passed: all nine KPI fields reconcile exactly |
| Lot quantity conservation and inventory valuation | Passed in automated tests |
| Expiry-day use, already expired stock, and quarantine exclusions | Passed controlled-fixture tests |
| FEFO order, tie handling, zero demand, and horizon exclusion | Passed controlled-fixture tests |
| Whole-count units and seeded reproducibility | Passed end-to-end tests |
| Dashboard JavaScript syntax | Passed |

The suite tests the stated educational model. It does not represent approval by a supply planner, Quality team, or employer. The broader user acceptance test plan includes cases and stakeholder review that remain separate from automated verification.

The generated SQLite file is excluded from the repository and can be rebuilt with `python3 src/analyze.py`. Published source CSVs, risk detail CSVs, JSON, SQL, and Python provide the reproducible evidence.
