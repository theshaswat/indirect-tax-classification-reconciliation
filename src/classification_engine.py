"""Applies the correct tax treatment to each invoice line and flags exceptions.

Mirrors the real AP tax-ops mechanic: every line carries a tax code from the vendor
master; this engine independently derives the code that *should* apply from the
jurisdiction + category rules table, and flags any line where the two disagree —
the exception queue a tax-ops analyst would work.
"""
from pathlib import Path
import csv

from tax_rules import load_rules

INVOICES_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "synthetic_invoice_lines.csv"
EXCEPTIONS_OUT = Path(__file__).resolve().parents[1] / "data" / "final" / "exception_queue.csv"
SUMMARY_OUT = Path(__file__).resolve().parents[1] / "outputs" / "tables" / "reconciliation_summary.csv"


def classify(invoices: list[dict], rules: list[dict]) -> list[dict]:
    rules_by_key = {(r["jurisdiction"], r["category"]): r for r in rules}
    results = []
    for line in invoices:
        rule = rules_by_key.get((line["jurisdiction"], line["category"]))
        status = "OK"
        reason = ""
        rate_pct = ""
        if rule is None:
            status = "EXCEPTION"
            reason = "No matching rule for jurisdiction/category — route to manual review"
        else:
            rate_pct = rule["rate_pct"]
            if not line["vendor_master_tax_code"]:
                status = "EXCEPTION"
                reason = "Vendor master tax code is blank — stale/never-set code"
            elif line["vendor_master_tax_code"] != line["correct_tax_code"]:
                status = "EXCEPTION"
                reason = (
                    f"Vendor master code '{line['vendor_master_tax_code']}' does not match "
                    f"derived code '{line['correct_tax_code']}' — likely stale code carried "
                    f"over from a different jurisdiction/category"
                )
            elif rule["confidence"] != "confirmed_this_session":
                status = "OK — VERIFY RATE"
                reason = "Rate is a stable known fact, not source-confirmed this session; verify before filing"

        results.append({
            **line,
            "derived_rate_pct": rate_pct,
            "status": status,
            "reason": reason,
        })
    return results


def reconcile_summary(classified: list[dict]) -> list[dict]:
    by_jurisdiction: dict[str, dict[str, int]] = {}
    for row in classified:
        j = row["jurisdiction"]
        by_jurisdiction.setdefault(j, {"total_lines": 0, "exceptions": 0, "ok": 0, "ok_verify_rate": 0})
        by_jurisdiction[j]["total_lines"] += 1
        if row["status"] == "EXCEPTION":
            by_jurisdiction[j]["exceptions"] += 1
        elif row["status"] == "OK":
            by_jurisdiction[j]["ok"] += 1
        else:
            by_jurisdiction[j]["ok_verify_rate"] += 1
    summary = []
    for j, counts in sorted(by_jurisdiction.items()):
        rate = round(100 * counts["exceptions"] / counts["total_lines"], 1)
        summary.append({"jurisdiction": j, **counts, "exception_rate_pct": rate})
    return summary


if __name__ == "__main__":
    with open(INVOICES_PATH, newline="", encoding="utf-8") as f:
        invoices = list(csv.DictReader(f))
    rules = load_rules()
    classified = classify(invoices, rules)
    summary = reconcile_summary(classified)

    EXCEPTIONS_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)

    exceptions_only = [r for r in classified if r["status"] != "OK"]
    with open(EXCEPTIONS_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(classified[0].keys()))
        writer.writeheader()
        writer.writerows(exceptions_only)

    with open(SUMMARY_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    total = len(classified)
    n_exceptions = sum(1 for r in classified if r["status"] == "EXCEPTION")
    print(f"Classified {total} lines. {n_exceptions} EXCEPTION ({round(100*n_exceptions/total,1)}%), "
          f"{sum(1 for r in classified if r['status']=='OK — VERIFY RATE')} OK-verify-rate, "
          f"{sum(1 for r in classified if r['status']=='OK')} clean OK.")
    print(f"Exception queue -> {EXCEPTIONS_OUT}")
    print(f"Reconciliation summary -> {SUMMARY_OUT}")
