# Data Dictionary

## `data/raw/tax_rules.csv`

| Field | Description |
|---|---|
| `jurisdiction` | India, US-{state}, or EU-{country code} |
| `tax_type` | GST, TDS, Sales & Use Tax, or VAT |
| `category` | The specific rate band/section within that tax type — this is the join key the classification engine matches on |
| `rate_pct` | The rate, as a percentage |
| `condition` | Plain-language scope/threshold for when this rate applies |
| `source` | The citing authority/report |
| `as_of_date` | Effective date or date the figure was pulled |
| `confidence` | `confirmed_this_session` (pulled and checked live) or `stable_fact_verify_before_filing` (well-established but not re-confirmed live) |

## `data/processed/synthetic_invoice_lines.csv`

| Field | Description |
|---|---|
| `invoice_id`, `line_id` | Synthetic identifiers |
| `jurisdiction`, `category` | Matches `tax_rules.csv`'s join keys |
| `counterparty_type` | individual / company / foreign_nonresident |
| `amount` | Illustrative line amount |
| `vendor_master_tax_code` | The code "on file" — may be correct, blank, or stale (1 in 3 lines) |
| `correct_tax_code` | The code the engine independently derives as correct |
| `note` | Plain-language scenario description |

## `data/final/exception_queue.csv`

All lines where `status != OK` — the working queue a tax-ops analyst would action, with a `reason`
field stating exactly why each line was flagged.

## `outputs/tables/reconciliation_summary.csv`

Exception rate by jurisdiction — the validation gate described in the Recommendation Memo.
