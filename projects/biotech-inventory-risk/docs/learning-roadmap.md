# Make this project your own

This repository was built with AI assistance as a starting portfolio case study. It demonstrates a reproducible analytical approach, not employment experience, a validated manufacturing system, or a measured operational improvement. Use the walkthrough after you can reproduce and explain the results yourself.

## First learning session

1. Run the generation, analysis, and test commands in the README.
2. Open the raw material and lot files. Pick one material and follow its lots into the dashboard.
3. Explain why quarantined and expired quantities cannot cover today's demand.
4. Trace one lot through the first-expiring-first-out calculation. Explain the date boundary and the cost calculation.
5. Run the SQL examples and reconcile their totals to the dashboard.

## Add your own analysis

- Change one material's daily demand and regenerate the analysis without regenerating the source data. Record how the expiry exposure and lead-time gap change, and explain why.
- Write a short executive memo comparing two actions: defer a purchase or pursue an approved alternative supplier. Document the assumptions before recommending an action.
- Add one useful test you designed independently, such as an expiry boundary or a second supplier option.
- Import the prepared CSVs into Excel or Power BI if you want to demonstrate those tools. Add the actual workbook or report only after building and checking it; the current web dashboard does not establish Power BI experience.

## Explain scope accurately

In an interview, separate what the code calculates from what a planner or Quality team would need to approve. Financial exposure is a modeled amount at risk, not booked loss or achieved savings. Quarantined stock is visible but is not released by this application. A real project would need approved demand, purchase-order arrivals, quality-release dates, operating procedures, and stakeholder validation.
