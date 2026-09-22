# Indirect Tax Classification & Reconciliation Engine

**Status: Phase 1–4 complete.** Data sourced, engine built and verified, reports written and
available as both Markdown and PDF (`reports/00_EXECUTIVE_SUMMARY`, `01_RECOMMENDATION_MEMO`,
`02_DATA_DICTIONARY`, `03_SOURCE_REGISTER`, `LIMITATIONS`), dashboard built
(`dashboards/dashboard.html`). Resume-ready line is in the Executive Summary — **read
`reports/LIMITATIONS.pdf` once before using it**, since several rates are flagged
unconfirmed-this-session.

## What this is

A rules-based engine that classifies AP invoice lines by the correct indirect-tax treatment
(GST, India TDS, US state Sales & Use Tax, EU VAT) and flags exceptions — mirroring the real
failure mode a tax-ops team manages: *a wrong or stale tax code on the vendor master is the
most common root cause of an exception queue.*

## Scope

- **In scope:** rule-based classification across 11 jurisdictions, 20 rate/category rules, sourced
  from primary regulatory tables (CBIC, Income Tax Act 1961/Income-tax Act 2025, Tax Foundation's
  read of state Departments of Revenue, the European Commission's VAT rates database). A synthetic
  invoice-line test set (60 lines) exercises the engine, including deliberately injected stale/wrong
  tax codes.
- **Out of scope:** no real vendor or transaction data exists anywhere for this — every invoice line
  is synthetic and labelled as such. No claim of SAP/Vertex/OneSource software experience. No local
  US sales-tax add-ons (county/city) — state base rate only.

## Data

`data/raw/tax_rules.csv` — 20 rules, each with a `source` and `as_of_date` column. 11 rows are
`confirmed_this_session` (pulled and checked in this build); 9 are `stable_fact_verify_before_filing`
(well-established rates — e.g. Ireland's 23% VAT, India's TDS section rates — not independently
re-confirmed against a live primary source this session). **The engine itself flags every line that
relies on an unconfirmed rate** rather than presenting all rates with equal confidence — see the
`OK — VERIFY RATE` status in the classification output.

## How it works

1. `src/tax_rules.py` loads the sourced rate table.
2. `src/generate_synthetic_invoices.py` builds 60 synthetic invoice lines across all 11
   jurisdictions, injecting a wrong/blank vendor-master tax code on 1 in 3 lines.
3. `src/classification_engine.py` independently derives the correct tax code per line from the
   rules table and compares it to the vendor-master code, producing an exception queue
   (`data/final/exception_queue.csv`) and a reconciliation summary by jurisdiction
   (`outputs/tables/reconciliation_summary.csv`).

Run: `cd src && python3 generate_synthetic_invoices.py && python3 classification_engine.py`

## What broke

The first run flagged a 66.7% exception rate — implausibly high. Root cause: the synthetic-data
generator used the rules table's `tax_type` value ("Sales & Use Tax", "VAT") where the classification
engine expected the `category` value ("State base rate", "Standard"), so every US and EU line failed
to match any rule at all and was misclassified as a missing-rule exception. Fixed by aligning the
generator's category labels to the rules table's actual `category` column; re-run produced the
expected, deterministic 33.3% exception rate (matching the 1-in-3 error-injection rate exactly),
confirming the engine's matching logic is now internally consistent.

## Reports (Phase 3–4)

`reports/00_EXECUTIVE_SUMMARY.{md,pdf}`, `01_RECOMMENDATION_MEMO.{md,pdf}`,
`02_DATA_DICTIONARY.{md,pdf}`, `03_SOURCE_REGISTER.{md,pdf}`, `LIMITATIONS.{md,pdf}`. Dashboard:
`dashboards/dashboard.html` (exception composition by jurisdiction, status-color coded).

## Not done

Re-confirm the 9 `stable_fact_verify_before_filing` rates against a live primary source before any
number from this project reaches a resume — see `reports/LIMITATIONS.pdf`.

## Author

**Shaswat Sharma** — [GitHub: theshaswat](https://github.com/theshaswat)

## License

MIT (see [`LICENSE`](LICENSE)).
