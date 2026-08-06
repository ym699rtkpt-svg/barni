
import subprocess
import tempfile
from pathlib import Path

from parser_engine import extract_items

CASES = [
    ("invoice_781", "מפגש הדייגים - חשבונית מס' 781  מתאריך  27-07-2026.pdf", 1),
    ("invoice_841", "חשבונית מס 841.pdf", 1),
    ("aleh_statement", "rptRikuzClients.pdf", 44),
    ("eden_david", "חשבונית2.pdf", 3),
    ("boaz_50346", "50346.pdf", 1),
    ("ymr_invoice10", "חשבונית10.pdf", 2),
    ("electra_7", "חשבונית7.PDF", 1),
    ("electra_8", "חשבונית8.PDF", 1),
]

INPUT = Path.home() / "restaurant-invoices" / "input"
passed = total = 0

for name, filename, expected in CASES:
    path = INPUT / filename

    if not path.exists():
        print(f"⚠️ {name}: חסר {filename}")
        continue

    with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
        subprocess.run(
            ["/opt/homebrew/bin/pdftotext", "-layout", str(path), tmp.name],
            check=True,
        )
        raw = Path(tmp.name).read_text(encoding="utf-8", errors="ignore")

    actual = len(extract_items(raw))
    total += 1

    if actual == expected:
        passed += 1
        print(f"✅ {name}: {actual} שורות")
    else:
        print(f"❌ {name}: התקבלו {actual}, צפויות {expected}")

score = 100 * passed / total if total else 0
print(f"\nציון שורות v07: {passed}/{total} = {score:.1f}%")
