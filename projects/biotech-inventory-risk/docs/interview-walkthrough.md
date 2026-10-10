# Interview walkthrough: 3–5 minutes

Use this as a speaking guide. Replace any claims about work completed with what you actually did. Do not memorize a script you cannot explain.

## 1. Business problem — about 40 seconds

“This is a fictional biotech raw-material planning case. A warehouse can have enough stock on paper and still be unable to support production, because some lots are quarantined or will expire before they are needed. I wanted to make that distinction visible to a planner and connect the inventory decision to cost exposure.”

Explain the three users: the planner needs usable supply, Finance needs a clear cost basis, and Quality needs status visibility. State immediately that all data is synthetic.

## 2. Requirements and data — about 50 seconds

Show one requirement and its acceptance criterion. Explain why inventory status, expiry date, forecast demand, material units, and replenishment lead time matter. Show a data-quality check you have run, such as rejection of duplicate lot identifiers or negative quantities.

“I defined eligibility separately from total stock. That prevents quarantined inventory from masking a shortage. I also wanted bad input to fail clearly, because a polished dashboard built on invalid data would give a misleading answer.”

## 3. Analysis — about 60 seconds

Show a short SQL query and one Python calculation you understand. Explain FEFO in plain language: consume the earliest-expiring eligible lot first. Explain the expiry-date boundary, the demand assumption, and how shortage before replenishment is identified.

Walk through one material with two lots using the actual result. Verify opening quantity equals consumed plus remaining quantity. Explain how unused expiring stock is valued. Call this **modeled exposure**, not money saved.

## 4. Decision and verification — about 60 seconds

Show the dashboard and choose one risk. Identify a reasonable follow-up: verify forecast demand, inspect release timing, review a potential expedite, or check alternative stock. Explain who would own the decision and which information is still missing.

Show the relevant UAT case and your actual test result. A useful example is demand above released stock but below total stock: the shortage should remain because quarantined supply is excluded.

## 5. Ownership and limits — about 40 seconds

“The repository includes AI-assisted scaffolding. The parts I personally reviewed and can explain are [name only the parts you have reviewed]. I changed [an actual change] and verified it with [an actual check]. The next step I would take is [a specific improvement].”

“This is a portfolio model. It does not claim GMP validation, real biotech data, hands-on SAP operation, or realized savings. A production version would need approved quality rules, ERP integration, actual orders and schedules, access controls, and further validation.”

## Prepare before presenting

- Run the project and explain its assumptions without reading from the screen.
- Understand one SQL query, one calculation, and one validation test well enough to change them.
- Record a real personal improvement, including why you made it and how you checked it.
- Use the actual output to tell one material-level story; do not invent a percentage saving.
- Be ready to explain why a good historical forecast still needs uncertainty and operational review.

## Likely follow-up questions

| Question | What your answer should demonstrate |
| --- | --- |
| Why exclude quarantined stock? | Quality release status controls planning eligibility; quantity alone is insufficient. |
| Why FEFO rather than FIFO? | Expiry order helps consume eligible stock before it becomes unusable; disclose exceptions the simplified model cannot represent. |
| What happens with no demand? | No consumption, explicit zero-demand handling, and possible expiry exposure. |
| How would you trust the dashboard? | Input validation, reconciliations, boundary tests, and traceability to a single analysis run. |
| What would change with real company data? | Actual forecast granularity, lot rules, unit conversions, order timing, production constraints, and approved access/quality processes. |
| What did you do yourself? | Specific reviewed code, tests, interpretation, and improvements; a clear distinction between assisted scaffolding and independent skill. |
