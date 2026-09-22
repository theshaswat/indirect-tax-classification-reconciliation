# Indirect Tax Classification & Reconciliation Engine — Executive Summary

**A rules-based engine that independently derives the correct indirect-tax treatment for an AP
invoice line and flags it when the vendor-master tax code disagrees — the exact mechanic behind a
tax-ops exception queue.**

## Headline result

- **20 rules sourced across 11 jurisdictions** — India GST (post-Sept-2025 4-slab reform) and TDS,
  US state Sales & Use Tax (CA/NY/IL/TX), EU VAT (DE/FR/LU/HU/IE/NL) — each with a citation and an
  `as_of_date`.
- **60 synthetic invoice lines, engine-classified with a 33.3% exception rate** — exactly matching
  the 1-in-3 error-injection rate built into the test set, confirming the classification logic is
  internally consistent (see Recommendation Memo, "What broke").
- **9 of 20 rules are flagged `stable_fact_verify_before_filing`** rather than presented with false
  confidence — the engine itself demotes any line relying on one of these to `OK — VERIFY RATE`
  instead of a clean pass.

## Resume-ready line

*"Built a rules-based indirect-tax classification engine spanning GST, TDS (India), Sales & Use Tax
(US), and VAT (EU) across 11 jurisdictions and 20 sourced rules; tested against 60 synthetic
invoice lines with a 33.3% exception-detection rate, independently verified to match the injected
error rate exactly."*

## What this is not

Not a real tax filing tool, not trained on or tested against any real vendor data (none exists for
this project), and not a claim of SAP/Vertex/OneSource software experience. It demonstrates the
underlying reasoning a tax-ops analyst applies — jurisdiction + transaction-type → correct
treatment → flag the mismatch — not production tax software.
