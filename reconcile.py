"""
Reconciliation and exception flagging tool
Author: Mohsin Rasheed

What this does
---------------
Takes two files that should describe the same transactions from two different
systems (an internal general ledger export and a bank statement), matches them
up automatically, and flags anything that does not line up cleanly, with a
plain language reason attached to each exception.

This mirrors the manual reconciliation work behind the compliance checklist
built at Meezan Bank, turned into a repeatable script instead of a manual
line by line check.
"""

import csv
from pathlib import Path

LEDGER_PATH = Path("data/general_ledger.csv")
BANK_PATH = Path("data/bank_statement.csv")
OUTPUT_PATH = Path("output/exceptions_report.csv")

AMOUNT_TOLERANCE = 0.01  # euros, treat tiny rounding differences as a match
DATE_TOLERANCE_DAYS = 1  # allow same day settlement lag without flagging


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(value):
    return round(float(value), 2)


def days_between(date_a, date_b):
    from datetime import datetime
    fmt = "%Y-%m-%d"
    return abs((datetime.strptime(date_a, fmt) - datetime.strptime(date_b, fmt)).days)


def reconcile(ledger_rows, bank_rows):
    exceptions = []

    # Index bank rows by reference, keeping every occurrence in case of duplicates
    bank_by_ref = {}
    for row in bank_rows:
        bank_by_ref.setdefault(row["reference"], []).append(row)

    seen_ledger_refs = {}

    for entry in ledger_rows:
        ref = entry["reference"]
        amount = to_float(entry["amount"])
        date = entry["date"]

        # Flag duplicate ledger entries (same reference appearing more than once)
        if ref in seen_ledger_refs:
            exceptions.append({
                "reference": ref,
                "issue": "Duplicate ledger entry",
                "detail": f"Reference {ref} appears more than once in the ledger "
                          f"for {amount:.2f} EUR. Likely a double entry rather than "
                          f"two separate transactions.",
            })
            continue
        seen_ledger_refs[ref] = True

        matches = bank_by_ref.get(ref)

        if not matches:
            exceptions.append({
                "reference": ref,
                "issue": "Missing on bank statement",
                "detail": f"Reference {ref} for {amount:.2f} EUR is recorded in the "
                          f"ledger but has not appeared on the bank statement. "
                          f"Likely an uncleared or in transit payment.",
            })
            continue

        bank_entry = matches[0]
        bank_amount = to_float(bank_entry["amount"])
        bank_date = bank_entry["date"]

        amount_diff = round(abs(amount - bank_amount), 2)
        date_gap = days_between(date, bank_date)

        if amount_diff > AMOUNT_TOLERANCE and date_gap <= DATE_TOLERANCE_DAYS:
            exceptions.append({
                "reference": ref,
                "issue": "Amount mismatch",
                "detail": f"Ledger shows {amount:.2f} EUR, bank shows "
                          f"{bank_amount:.2f} EUR, a difference of {amount_diff:.2f} EUR "
                          f"on the same date. Likely a data entry error such as a "
                          f"transposed digit rather than a timing issue.",
            })
        elif date_gap > DATE_TOLERANCE_DAYS and amount_diff <= AMOUNT_TOLERANCE:
            exceptions.append({
                "reference": ref,
                "issue": "Timing difference",
                "detail": f"Same amount ({amount:.2f} EUR) but posted {date_gap} days "
                          f"apart between the ledger ({date}) and the bank ({bank_date}). "
                          f"Likely a normal settlement delay, not an error, but worth "
                          f"confirming if the gap grows in future periods.",
            })
        elif amount_diff > AMOUNT_TOLERANCE and date_gap > DATE_TOLERANCE_DAYS:
            exceptions.append({
                "reference": ref,
                "issue": "Amount and timing mismatch",
                "detail": f"Ledger shows {amount:.2f} EUR on {date}, bank shows "
                          f"{bank_amount:.2f} EUR on {bank_date}. Both the amount and "
                          f"the date differ, so this needs manual review rather than "
                          f"an automatic explanation.",
            })

    # Anything on the bank statement with a reference never seen in the ledger at all
    ledger_refs = set(seen_ledger_refs.keys())
    for ref, rows in bank_by_ref.items():
        if ref not in ledger_refs:
            for row in rows:
                exceptions.append({
                    "reference": ref,
                    "issue": "Missing on ledger",
                    "detail": f"Reference {ref} for {to_float(row['amount']):.2f} EUR "
                              f"appears on the bank statement but was never recorded "
                              f"in the ledger. Common cause: bank fees or charges that "
                              f"post automatically without a matching journal entry.",
                })

    return exceptions


def write_report(exceptions, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["reference", "issue", "detail"])
        writer.writeheader()
        writer.writerows(exceptions)


def main():
    ledger_rows = load_rows(LEDGER_PATH)
    bank_rows = load_rows(BANK_PATH)

    exceptions = reconcile(ledger_rows, bank_rows)

    print(f"Checked {len(ledger_rows)} ledger entries against {len(bank_rows)} bank entries.")
    print(f"Found {len(exceptions)} exceptions:\n")

    for item in exceptions:
        print(f"[{item['issue']}] {item['reference']}")
        print(f"  {item['detail']}\n")

    write_report(exceptions, OUTPUT_PATH)
    print(f"Full report written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
