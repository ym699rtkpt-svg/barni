from __future__ import annotations


def classify_invoice_line(description: str) -> str:
    """
    Classify invoice lines into business categories.
    """

    if not description:
        return "product"

    text = description.strip().lower()

    # Totals
    if any(x in text for x in (
        'סה"כ',
        "סהכ",
        "סך הכל",
        "לתשלום",
        "total",
    )):
        return "total"

    # VAT
    if any(x in text for x in (
        'מע"מ',
        "מעמ",
        "vat",
    )):
        return "vat"

    # Discount
    if any(x in text for x in (
        "הנחה",
        "discount",
    )):
        return "discount"

    # Payment
    if any(x in text for x in (
        "ויזה",
        "אשראי",
        "מאסטר",
        "מזומן",
        "כרטיס",
    )):
        return "payment"

    # Notes
    if any(x in text for x in (
        "הערה",
        "remarks",
        "note",
    )):
        return "note"

    return "product"