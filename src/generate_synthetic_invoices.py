"""Generates a synthetic AP invoice-line test set spanning jurisdictions and edge cases.

No real vendor or transaction data exists for this project — these rows are illustrative
test cases only, built to exercise the classification engine's rule matching and exception
handling, not to represent any real company's invoices.
"""
from pathlib import Path
import csv
import random

random.seed(42)

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "synthetic_invoice_lines.csv"

# (jurisdiction, category, counterparty_type, transaction_note)
SCENARIOS = [
    ("India", "Standard", "company", "Domestic vendor — office supplies"),
    ("India", "Nil-rated essential", "company", "Domestic vendor — staff canteen food grains"),
    ("India", "Reduced", "company", "Domestic vendor — footwear under revised slab"),
    ("India", "Luxury/sin", "company", "Fleet vehicle purchase, >1500cc diesel"),
    ("India", "194C - Contractor (individual/HUF)", "individual", "Freelance contractor — office fit-out"),
    ("India", "194C - Contractor (other entities)", "company", "Facilities contractor — annual AMC"),
    ("India", "194J - Professional fees", "individual", "External legal counsel retainer"),
    ("India", "194J - Technical services", "company", "IT technical support services"),
    ("India", "194Q - Purchase of goods", "company", "Bulk stationery purchase, seller turnover >INR 50L"),
    ("India", "195 - Foreign remittance (no treaty relief)", "foreign_nonresident", "Royalty payment to non-resident licensor, no TRC on file"),
    ("US-CA", "State base rate", "company", "SaaS subscription — nexus established"),
    ("US-NY", "State base rate", "company", "Office equipment purchase"),
    ("US-IL", "State base rate", "company", "Marketing services vendor"),
    ("US-TX", "State base rate", "company", "Hardware purchase, in-state vendor"),
    ("EU-DE", "Standard", "company", "Consulting services, intra-EU B2B (reverse charge candidate)"),
    ("EU-FR", "Standard", "company", "Domestic French vendor — event services"),
    ("EU-LU", "Standard", "company", "Cross-border digital services vendor"),
    ("EU-HU", "Standard", "company", "Domestic Hungarian vendor — logistics"),
    ("EU-IE", "Standard", "company", "Domestic Irish vendor — office lease"),
    ("EU-NL", "Standard", "company", "Domestic Dutch vendor — software licence"),
]

# Deliberately-wrong or missing tax codes injected to create real exceptions,
# mirroring the stated failure mode: "a wrong or stale tax code is the single
# most common root cause of a tax ops exception queue."
INJECT_ERROR_EVERY_N = 3


def build_rows(n_per_scenario: int = 3) -> list[dict]:
    rules_by_key = {}
    from tax_rules import load_rules
    for r in load_rules():
        rules_by_key.setdefault((r["jurisdiction"], r["category"]), r)

    rows = []
    invoice_counter = 1000
    line_counter = 1
    for jurisdiction, category, counterparty, note in SCENARIOS:
        rule = rules_by_key.get((jurisdiction, category))
        correct_code = f"{jurisdiction}-{category.split(' - ')[0].replace(' ', '_')}"
        for i in range(n_per_scenario):
            invoice_counter += 1
            amount = round(random.uniform(500, 250000), 2)
            vendor_master_code = correct_code
            if (line_counter % INJECT_ERROR_EVERY_N) == 0:
                # inject a stale/wrong code: either blank, or a code from a different jurisdiction
                other = random.choice([s for s in SCENARIOS if s[0] != jurisdiction])
                vendor_master_code = random.choice([
                    "",
                    f"{other[0]}-{other[1].split(' - ')[0].replace(' ', '_')}",
                ])
            rows.append({
                "invoice_id": f"INV-{invoice_counter}",
                "line_id": line_counter,
                "jurisdiction": jurisdiction,
                "category": category,
                "counterparty_type": counterparty,
                "amount": amount,
                "vendor_master_tax_code": vendor_master_code,
                "correct_tax_code": correct_code,
                "note": note,
            })
            line_counter += 1
    return rows


if __name__ == "__main__":
    rows = build_rows()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic invoice lines to {OUT_PATH}")
