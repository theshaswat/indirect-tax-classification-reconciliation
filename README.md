# Indirect Tax Classification & Reconciliation Engine

> A rules-based engine that independently derives the correct indirect-tax treatment for
> an AP invoice line and flags it when the vendor-master tax code disagrees — the mechanic
> behind a tax-ops exception queue, across 11 jurisdictions and 20 sourced rate rules.

## Question

The most common root cause of a tax-ops exception queue is not a mis-keyed amount — it is
a wrong or stale tax code sitting on the vendor master, applied correctly by the system to
every invoice that vendor sends. What does it take to catch that automatically, and how do
you avoid a tool that asserts a rate it cannot actually stand behind?

## Findings

| | |
|---|---|
| **Rules sourced** | **20**, across **11 jurisdictions**, each with a citation and an `as_of_date` |
| Coverage | India GST (post-Sept-2025 four-slab reform) and TDS · US state Sales & Use Tax (CA/NY/IL/TX) · EU VAT (DE/FR/LU/HU/IE/NL) |
| Test set | **60 synthetic invoice lines**, with a wrong or blank vendor-master code injected on 1 in 3 |
| **Exception rate detected** | **33.3%** — matching the injected error rate exactly, in every one of the 11 jurisdictions |
| Rate confidence | **11 of 20** rules confirmed against a primary source in this build; **9 of 20** flagged `stable_fact_verify_before_filing` |
| Confidence handling | The engine demotes any line resting on an unconfirmed rate to `OK — VERIFY RATE` rather than passing it clean |

Recovering the injected rate is a test result rather than a business finding: it says the
classifier agrees with ground truth on a set where ground truth is known by construction.
Without real vendor data that is the only property available to verify.

Nine of the twenty rates are well-established figures that were not independently
re-confirmed against a live primary source for this build. Rather than presenting all
twenty with equal confidence, the engine propagates that distinction into every line it
touches, so a reviewer sees which conclusions rest on a checked rate and which do not.

Per-jurisdiction detail: [`outputs/tables/reconciliation_summary.csv`](outputs/tables/reconciliation_summary.csv).
Full reasoning: [`reports/01_RECOMMENDATION_MEMO.md`](reports/01_RECOMMENDATION_MEMO.md).

## Method

1. `src/tax_rules.py` loads the sourced rate table, carrying each rule's citation,
   `as_of_date` and confidence tier.
2. `src/generate_synthetic_invoices.py` builds 60 invoice lines spanning all 11
   jurisdictions, injecting a wrong or blank vendor-master tax code on 1 in 3.
3. `src/classification_engine.py` derives the correct code per line **independently of the
   code already on the line**, compares the two, and writes an exception queue
   (`data/final/exception_queue.csv`) plus a reconciliation summary by jurisdiction.

Step 3 has to derive the code independently, because an engine that reads the existing
code as an input cannot detect that the existing code is wrong.

## A failure worth recording

The first run returned a 66.7% exception rate — implausibly high, and the reason it was
worth chasing rather than reporting. Root cause: the synthetic-data generator wrote the
rules table's `tax_type` value ("Sales & Use Tax", "VAT") into a field where the
classification engine expected the `category` value ("State base rate", "Standard"). Every
US and EU line therefore matched no rule at all and was misclassified as a missing-rule
exception rather than as a code mismatch.

Aligning the generator's category labels to the rules table's actual `category` column
produced the expected, deterministic 33.3% — matching the injection rate exactly, in every
jurisdiction. Had the 66.7% been accepted rather than chased, it would have been reported
as a finding about tax-code hygiene when it was a field-mapping error.

## Structure

```
indirect-tax-classification-reconciliation/
├── data/
│   ├── raw/           # tax_rules.csv — 20 rules, each with source + as_of_date
│   ├── processed/     # synthetic_invoice_lines.csv — the 60-line test set
│   └── final/         # exception_queue.csv
├── src/
│   ├── tax_rules.py                  # sourced rate table loader
│   ├── generate_synthetic_invoices.py# test-set builder with error injection
│   ├── classification_engine.py      # independent derivation + reconciliation
│   └── build_pdf.py                  # renders reports/*.md to PDF
├── outputs/tables/    # reconciliation_summary.csv — by jurisdiction
├── dashboards/        # dashboard.html — exception composition by jurisdiction
└── reports/           # executive summary, memo, data dictionary,
                       # source register, limitations (.md + .pdf)
```

## How to run

```bash
pip install -r requirements.txt
cd src
python3 generate_synthetic_invoices.py   # -> data/processed/synthetic_invoice_lines.csv
python3 classification_engine.py         # -> data/final/exception_queue.csv,
                                         #    outputs/tables/reconciliation_summary.csv
python3 build_pdf.py                     # -> reports/*.pdf
```

## Data and sources

`data/raw/tax_rules.csv` — 20 rules drawn from primary regulatory tables: CBIC for India
GST, the Income Tax Act 1961 / Income-tax Act 2025 for TDS, the Tax Foundation's
compilation of state Departments of Revenue for US Sales & Use Tax, and the European
Commission's VAT rates database for EU VAT. Each row carries a `source`, an `as_of_date`,
and a confidence tier.

Full register: [`reports/03_SOURCE_REGISTER.md`](reports/03_SOURCE_REGISTER.md).
Field definitions: [`reports/02_DATA_DICTIONARY.md`](reports/02_DATA_DICTIONARY.md).

## Limitations

Full detail in [`reports/LIMITATIONS.md`](reports/LIMITATIONS.md). Headline items:

- **Every invoice line is synthetic.** No real vendor or transaction data is used anywhere
  in this project, and the exception rate reflects an injected error rate, not an observed
  one.
- **Nine of twenty rates are unconfirmed in this build** and are flagged as such. They
  should be re-checked against a live primary source before any figure here is relied on.
- **US coverage is state base rate only** — no county or city add-ons.
- This demonstrates the reasoning a tax-ops analyst applies (jurisdiction plus
  transaction type to correct treatment, then flag the mismatch). It is not production tax
  software, and implies no SAP, Vertex or OneSource experience.

## Author

**Shaswat Sharma** — [GitHub: theshaswat](https://github.com/theshaswat)

## License

MIT (see [`LICENSE`](LICENSE)).
