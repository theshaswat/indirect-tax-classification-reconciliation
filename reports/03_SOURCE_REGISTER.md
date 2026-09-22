# Source Register

| # | Source | Used for | Pulled |
|---|---|---|---|
| 1 | CBIC GST rate notifications (cbic-gst.gov.in) and coverage of the 56th GST Council reform | India GST 4-slab structure (0/5/18/40%), effective 22 Sept 2025 | 22 Sep 2026 |
| 2 | Income Tax Act 1961 sections 194C, 194J, 194Q, 195 (pre-1-Apr-2026 numbering; consolidated under Income-tax Act 2025 Section 393 from FY 2026-27) | India TDS/withholding rates and thresholds | 22 Sep 2026 |
| 3 | Tax Foundation — State and Local Sales Tax Rates, Midyear 2026 | US state base Sales & Use Tax rates (CA, NY, IL) | 22 Sep 2026 |
| 4 | Widely-reported stable Texas state rate (verify at comptroller.texas.gov) | US-TX base rate | 22 Sep 2026 |
| 5 | European Commission VAT rates database (via Tax Foundation's 2026 EU VAT summary, verified against EC data 3 Aug 2026) | EU VAT standard rates (DE, FR, LU, HU) | 22 Sep 2026 |
| 6 | Widely-reported stable rates (verify at revenue.ie / belastingdienst.nl) | EU-IE, EU-NL VAT rates | 22 Sep 2026 |

Every row above also appears in `data/raw/tax_rules.csv` with its own `source` and `confidence`
column — this file is the narrative register; the CSV is the machine-readable one, and the two are
kept consistent by hand.
