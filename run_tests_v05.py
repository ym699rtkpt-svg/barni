
import json
import math
import subprocess
import tempfile
from pathlib import Path
from parser_engine import parse_invoice, extract_items

BASE = Path(__file__).resolve().parent
EXPECTED = json.loads((BASE / "expected_v05.json").read_text(encoding="utf-8"))

FILES = {
    "baba_781": Path.home() / "restaurant-invoices" / "input" / "מפגש הדייגים - חשבונית מס' 781  מתאריך  27-07-2026.pdf",
    "michal_841": Path.home() / "restaurant-invoices" / "input" / "חשבונית מס 841.pdf",
    "aleh_statement": Path.home() / "restaurant-invoices" / "input" / "rptRikuzClients.pdf",
}

def close_enough(actual, expected):
    if isinstance(expected, float):
        return actual is not None and math.isclose(float(actual), expected, abs_tol=0.02)
    return actual == expected

passed = total = 0

for key, path in FILES.items():
    if not path.exists():
        print(f"⚠️ {key}: הקובץ לא נמצא ב-{path}")
        continue

    with tempfile.NamedTemporaryFile(suffix=".txt") as temp:
        subprocess.run(
            ["/opt/homebrew/bin/pdftotext", "-layout", str(path), temp.name],
            check=True
        )
        text = Path(temp.name).read_text(encoding="utf-8", errors="ignore")

    result = parse_invoice(text)
    items = extract_items(text)
    failures = []

    for field, wanted in EXPECTED[key].items():
        total += 1
        actual = len(items) if field == "item_count" else result.get(field)
        if close_enough(actual, wanted):
            passed += 1
        else:
            failures.append(f"{field}: התקבל {actual!r}, צפוי {wanted!r}")

    if failures:
        print(f"❌ {key}")
        for failure in failures:
            print(f"   {failure}")
    else:
        print(f"✅ {key}")

score = 100 * passed / total if total else 0
print(f"\nציון v05: {passed}/{total} = {score:.1f}%")
