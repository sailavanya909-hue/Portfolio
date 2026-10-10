# Biotech Inventory & Expiry Risk

A supply chain business analyst portfolio project: use lot-level inventory and demand data to identify materials at risk of shortage or expiry, then explain the decisions to a planner, Finance, and Quality.

**All data is synthetic.** This is a learning scenario, not a validated production planning system. It does not represent an actual biotech company's operations or establish GMP compliance, SAP experience, or realized savings.

## Business problem

A fictional biotech manufacturer has inventory on hand, but some lots are quarantined and others may expire before they can be consumed. A stock-total report can therefore hide a shortage. The planner needs to understand which released lots can meet forecast demand, where lead times create a supply gap, and which inventory needs attention before its expiry date.

## Published scenario findings

The October 9, 2026 snapshot contains **12 materials, 52 lots, and 4 fictional suppliers**. It models **$106,048.38 in released expiry exposure** and **3 materials with a lead-time supply gap**. Exposure includes $12,712.00 already expired; it is not achieved savings.

Start with the [executive summary](docs/executive-summary.md), [interactive dashboard](https://sailavanya909-hue.github.io/Portfolio/projects/biotech-inventory-risk/site/), or [calculation methodology](docs/methodology.md).

## Decisions supported

| Audience | Question | Output to review |
| --- | --- | --- |
| Supply planner | Which materials may run short before replenishment can arrive? | Material-level shortage and coverage analysis |
| Supply planner | Which lots should be consumed first? | First-expiry-first-out (FEFO) allocation |
| Finance | What inventory value is exposed to expiry? | Unconsumed expiring stock valued at the modeled unit cost |
| Quality | Does planning exclude lots that are not released? | Lot status and eligibility checks |

These outputs flag decisions for review. They do not authorize a lot release, supplier expedite, purchase order, or change to a manufacturing plan.

## What this project demonstrates

- **Business analysis:** stakeholder needs, scope, requirements, acceptance criteria, and UAT cases.
- **Data quality:** validation of identifiers, dates, status, quantities, and costs before analysis.
- **SQL:** auditable inventory and risk queries.
- **Python:** reproducible synthetic data and a transparent planning model using the standard library.
- **Dashboard communication:** explain risk, drill into material and lot details, and show assumptions alongside results.

The project demonstrates planning concepts and analytical work. It does not demonstrate hands-on operation of SAP or a regulated quality management system.

## Run locally

The project lives inside the existing [Portfolio repository](https://github.com/sailavanya909-hue/Portfolio/tree/main/projects/biotech-inventory-risk). After cloning that repository, enter the project directory:

```bash
git clone https://github.com/sailavanya909-hue/Portfolio.git
cd Portfolio/projects/biotech-inventory-risk
```

From this project directory, using Python 3.9 or newer:

```bash
python3 src/generate_data.py
python3 src/analyze.py
python3 src/query_sql.py
python3 -m unittest discover -s tests -v
python3 -m http.server 8000 --directory site
```

Open <http://localhost:8000> for the dashboard. Serve it over HTTP: opening the HTML directly as a file will not load its JSON data reliably. The analyzer automatically refreshes `site/dashboard.json`. Review the analysis output and model assumptions before drawing conclusions. The written executive summary describes the published baseline; update it separately if you change the scenario.

Defaults: snapshot **October 9, 2026**, seed **42**, and a **90-day horizon through January 6, 2027**. The generator accepts `--seed` and `--as-of`; the analyzer accepts `--as-of` and `--horizon`. Keep the snapshot date consistent between generation and analysis.

## Repository guide

| Path | Purpose |
| --- | --- |
| `src/generate_data.py` | Generate reproducible, fictional input data |
| `src/analyze.py` | Validate inputs and calculate planning risks |
| `data/raw/` | Synthetic suppliers, materials, and lot CSV files |
| `data/processed/` | Dashboard JSON, lot/material risk details, and an executive summary |
| `sql/` | SQL analysis and reconciliation queries |
| `site/` | Static dashboard for local viewing and GitHub Pages |
| `tests/` | Model and validation checks |
| `docs/business-requirements.md` | Business scope, decision rules, and acceptance criteria |
| `docs/uat-plan.md` | User acceptance tests and expected outcomes |
| `docs/interview-walkthrough.md` | A short explanation for a recruiter or hiring manager |
| `docs/data-dictionary.md` | Source fields, joins, units, and cost definitions |
| `docs/verification.md` | Executed calculation and reconciliation checks |
| [Learning roadmap](docs/learning-roadmap.md) | Personal practice and improvements to complete before interviews |

## Interpretation and limitations

The model allocates constant daily demand to released lots in expiry order, with lot ID as the tie-breaker. A lot is usable **through its expiry date**; lots already expired at the snapshot are unavailable. Quarantined lots stay excluded throughout the simulation.

Three measures answer different questions:

| Measure | Meaning |
| --- | --- |
| Days of supply | Usable starting quantity divided by daily demand; this simple ratio ignores future expiry |
| FEFO coverage | Uninterrupted demand coverage in the simulation, including the fraction of the first partially filled day; capped at the horizon |
| Lead-time gap | Cumulative unserved demand during the material's lead-time window, valued at the material's replacement unit cost |

Coverage and days of supply are undefined for zero demand and shown accordingly. Lead-time gap is zero when demand is zero. Quantities are kept in each material's unit; liters, kilograms, vials, and other units are not added together.

Released expiry exposure includes stock already expired at the snapshot plus released stock left unconsumed when it expires during the horizon. It uses each lot's acquisition cost and excludes quarantined stock. Inventory exposure is a modeled cost value, not a booked write-off or a promised saving.

The simulation has no receipts, backorders, substitution, or safety stock. Demand uncertainty, production schedules, batch requirements, supplier capacity, quality release timing, and real purchase-order commitments can change a planning decision. Synthetic data cannot establish commercial impact or predict an actual company's results. The requirements and UAT plan define the intended behavior; the implementation and test results provide the evidence of what has been built.

## Portfolio ownership

This repository includes AI-assisted scaffolding. A candidate should explain which parts they reviewed, tested, modified, and can reproduce independently. Keep a record of those changes and describe simulated outcomes as simulated outcomes.

Project name: `biotech-inventory-risk`.

[View the GitHub Pages dashboard](https://sailavanya909-hue.github.io/Portfolio/projects/biotech-inventory-risk/site/).
