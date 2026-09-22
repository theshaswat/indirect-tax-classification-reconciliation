"""Loads the sourced jurisdiction/tax-type rate table and exposes a lookup used by the classification engine."""
from pathlib import Path
import csv

RULES_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "tax_rules.csv"


def load_rules(path: Path = RULES_PATH) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def find_rule(rules: list[dict], jurisdiction: str, category: str) -> list[dict]:
    return [r for r in rules if r["jurisdiction"] == jurisdiction and r["category"] == category]


if __name__ == "__main__":
    rules = load_rules()
    print(f"Loaded {len(rules)} rules across {len({r['jurisdiction'] for r in rules})} jurisdictions.")
    unverified = [r for r in rules if r["confidence"] != "confirmed_this_session"]
    print(f"{len(unverified)} rows flagged stable_fact_verify_before_filing — not confirmed live this session.")
