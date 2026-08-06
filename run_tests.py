
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from parser_engine import parse_invoice, extract_items


def close_enough(actual, expected):
    if isinstance(expected, float):
        return actual is not None and math.isclose(float(actual), expected, abs_tol=0.02)
    return actual == expected


def main():
    project = Path(__file__).resolve().parent
    expected = json.loads((project / "expected.json").read_text(encoding="utf-8"))
    invoice_dir = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / "restaurant-invoices" / "input"

    total_checks = 0
    passed_checks = 0
    print(f"\nבדיקת חשבוניות מתוך: {invoice_dir}\n")

    for name, wanted in expected.items():
        matches = list(invoice_dir.glob(f"{name}.*"))
        if not matches:
            print(f"{name}: לא נמצא קובץ")
            continue

        pdf = matches[0]
        with tempfile.NamedTemporaryFile(suffix=".txt") as temp:
            subprocess.run(
                ["/opt/homebrew/bin/pdftotext", "-layout", str(pdf), temp.name],
                check=True
            )
            text = Path(temp.name).read_text(encoding="utf-8", errors="ignore")

        result = parse_invoice(text)
        items = extract_items(text)
        failures = []

        for field, expected_value in wanted.items():
            total_checks += 1
            actual_value = len(items) if field == "item_count" else result.get(field)
            if close_enough(actual_value, expected_value):
                passed_checks += 1
            else:
                failures.append(f"{field}: התקבל {actual_value!r}, צפוי {expected_value!r}")

        if failures:
            print(f"❌ {name}")
            for failure in failures:
                print(f"   {failure}")
        else:
            print(f"✅ {name}")

    score = 100 * passed_checks / total_checks if total_checks else 0
    print(f"\nציון: {passed_checks}/{total_checks} = {score:.1f}%\n")


if __name__ == "__main__":
    main()
