
import json
import math
import subprocess
import tempfile
from pathlib import Path

from parser_engine import parse_invoice, extract_items

INPUT = Path.home() / "restaurant-invoices" / "input"

CASES = [
    {
        "name": "baba_781",
        "filename": "מפגש הדייגים - חשבונית מס' 781  מתאריך  27-07-2026.pdf",
        "expected": {
            "document_type": "חשבונית מס",
            "supplier": "בבאיי משה",
            "invoice_number": "781",
            "invoice_date": "2026-07-27",
            "subtotal": 2800.0,
            "vat": 504.0,
            "total": 3304.0,
            "item_count": 1,
        },
    },
    {
        "name": "michal_841",
        "filename": "חשבונית מס 841.pdf",
        "expected": {
            "document_type": "חשבונית מס",
            "supplier": "מיכל עלים בגבעה",
            "invoice_number": "841",
            "invoice_date": "2026-07-31",
            "subtotal": 1043.35,
            "vat": 0.0,
            "total": 1043.35,
            "item_count": 1,
        },
    },
    {
        "name": "aleh_statement",
        "filename": "rptRikuzClients.pdf",
        "expected": {
            "document_type": "ריכוז חשבון",
            "supplier": 'עלה עלה בע"מ',
            "invoice_date": "2026-06-01",
            "subtotal": 1768.8,
            "vat": 21.53,
            "total": 1790.33,
            "item_count": 44,
        },
    },
]

passed = total = 0

for case in CASES:
    path = INPUT / case["filename"]
    if not path.exists():
        print(f"⚠️ {case['name']}: לא נמצא {path}")
        continue

    with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
        subprocess.run(
            ["/opt/homebrew/bin/pdftotext", "-layout", str(path), tmp.name],
            check=True
        )
        raw = Path(tmp.name).read_text(encoding="utf-8", errors="ignore")

    parsed = parse_invoice(raw)
    items = extract_items(raw)
    failures = []

    for field, wanted in case["expected"].items():
        total += 1
        actual = len(items) if field == "item_count" else parsed.get(field)
        if isinstance(wanted, float):
            ok = actual is not None and math.isclose(float(actual), wanted, abs_tol=0.02)
        else:
            ok = actual == wanted

        if ok:
            passed += 1
        else:
            failures.append(f"{field}: התקבל {actual!r}, צפוי {wanted!r}")

    if failures:
        print(f"❌ {case['name']}")
        for failure in failures:
            print(f"   {failure}")
    else:
        print(f"✅ {case['name']}")

score = 100 * passed / total if total else 0
print(f"\nציון v06: {passed}/{total} = {score:.1f}%")
