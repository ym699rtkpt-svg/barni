
from __future__ import annotations

from collections import Counter

from database import connect, update_invoice


RULES = {
    "מזון": {
        "דגים": ["דג", "סלמון", "טונה", "דניס", "קבב דג"],
        "בשר": ["בשר", "עוף", "קבב", "אנטריקוט", "פרגית"],
        "ירקות": ["עגב", "בצל", "מלפפון", "חסה", "ירק", "פטרוזיליה"],
        "חלב": ["חלב", "גבינה", "שמנת", "יוגורט"],
        "כללי": ["מזון", "מטבח", "סופר", "קפה"],
    },
    "משקאות": {
        "אלכוהול": ["בירה", "יין", "וודקה", "אלכוהול"],
        "קלים": ["קולה", "מים מינרליים", "סודה", "משקה"],
    },
    "תפעול": {
        "מים": ["מים", "צריכת מים", "מודול מים"],
        "חשמל": ["חשמל", "קוטש", "קוט״ש"],
        "גז": ["גז", "בלון"],
        "ניקיון": ["ניקיון", "סבון", "אקונומיקה", "חומר ניקוי"],
        "תחזוקה": ["תחזוקה", "תיקון", "חלפים", "מחשב"],
    },
    "שירותים": {
        "ביטוח": ["ביטוח", "הפניקס", "פוליסה"],
        "ארנונה": ["ארנונה", "עירייה"],
        "משלוחים": ["משלוח", "הובלה", "שליח"],
    },
    "ציוד": {
        "חד פעמי": ["חד פעמי", "כוס", "צלחת", "סכו״ם"],
        "ציוד מטבח": ["ציוד", "מטבח", "סיר", "מחבת"],
        "מחשוב": ["מחשב", "מדפסת", "מסך", "טונר"],
    },
}


def classify_text(text: str) -> tuple[str, str]:
    text = (text or "").lower()
    matches = []

    for category, subcategories in RULES.items():
        for subcategory, keywords in subcategories.items():
            score = sum(keyword.lower() in text for keyword in keywords)
            if score:
                matches.append((score, category, subcategory))

    if not matches:
        return "לא מסווג", ""

    matches.sort(reverse=True)
    _, category, subcategory = matches[0]
    return category, subcategory


def classify_invoice(invoice_id: int) -> tuple[str, str]:
    with connect() as connection:
        invoice = connection.execute(
            "SELECT supplier, document_type FROM invoices WHERE id = ?",
            (invoice_id,),
        ).fetchone()
        items = connection.execute(
            "SELECT description FROM invoice_items WHERE invoice_id = ?",
            (invoice_id,),
        ).fetchall()

    text = " ".join([
        invoice["supplier"] if invoice else "",
        invoice["document_type"] if invoice else "",
        *[item["description"] for item in items],
    ])
    category, subcategory = classify_text(text)
    update_invoice(
        invoice_id,
        {"category": category, "subcategory": subcategory},
    )
    return category, subcategory


def classify_all() -> dict:
    with connect() as connection:
        ids = [
            row["id"]
            for row in connection.execute(
                "SELECT id FROM invoices"
            ).fetchall()
        ]

    counts = Counter()
    for invoice_id in ids:
        category, subcategory = classify_invoice(invoice_id)
        counts[f"{category}/{subcategory}"] += 1

    return {
        "processed": len(ids),
        "categories": dict(counts),
    }
