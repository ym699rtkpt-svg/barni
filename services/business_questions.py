from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import pandas as pd

from knowledge_engine.line_classifier import is_product_line
from database import (
    dashboard_data,
    month_summary,
    natural_language_query,
    product_price_change_summary,
    product_price_history,
)


_PRODUCT_ALIASES = {
    "milk": ("milk", "חלב"),
    "חלב": ("חלב", "milk"),
}


def _is_hebrew(value: str) -> bool:
    return bool(re.search(r"[\u0590-\u05ff]", value))


def _product_descriptions() -> list[str]:
    items = dashboard_data()["items"]
    if items.empty or "description" not in items.columns:
        return []
    if not items.empty:
        items = items[
            items.apply(lambda row: is_product_line(row.to_dict()), axis=1)
        ]
    return sorted(
        {
            str(value).strip()
            for value in items["description"].dropna()
            if str(value).strip()
        },
        key=len,
    )


def _match_product(question: str) -> tuple[str | None, bool]:
    lowered = question.casefold()
    descriptions = _product_descriptions()

    search_terms: list[str] = []
    for alias, equivalents in _PRODUCT_ALIASES.items():
        if alias in lowered:
            search_terms.extend(equivalents)

    if not search_terms:
        stop_words = {
            "what", "is", "the", "price", "of", "who", "supplies", "supplier",
            "which", "product", "increased", "most", "מה", "המחיר", "של", "מי",
            "הספק", "איזה", "מוצר", "התייקר", "הכי", "הרבה",
        }
        search_terms = [
            token for token in re.findall(r"[\w\u0590-\u05ff]+", lowered)
            if len(token) > 1 and token not in stop_words
        ]

    matches = [
        description
        for description in descriptions
        if any(term.casefold() in description.casefold() for term in search_terms)
    ]
    if not matches:
        return None, False

    match = min(matches, key=len)
    exact = any(match.casefold() == term.casefold() for term in search_terms)
    return match, exact


def _product_price_answer(question: str) -> dict[str, Any]:
    product, exact = _match_product(question)
    hebrew = _is_hebrew(question)
    if not product:
        message = (
            "לא מצאתי מוצר תואם בזיכרון העסקי. נסו להשתמש בשם שמופיע בחשבונית."
            if hebrew else
            "I couldn't find a matching product in Business Memory. Try the name shown on the invoice."
        )
        return {"route": "product", "understood": True, "message": message}

    history = product_price_history(product)
    priced = history[history["unit_price"].notna()] if not history.empty else history
    if priced.empty:
        message = (
            f"מצאתי את {product}, אבל אין עבורו מחיר יחידה שמור."
            if hebrew else f"I found {product}, but no unit price is stored for it."
        )
        return {"route": "product", "understood": True, "message": message}

    latest = priced.iloc[-1]
    price = float(latest["unit_price"])
    supplier = str(latest.get("supplier") or "").strip()
    date = str(latest.get("invoice_date") or "").strip()
    match_note = "" if exact else ("ההתאמה הקרובה ביותר היא " if hebrew else "The closest stored match is ")
    if hebrew:
        message = f"{match_note}{product}: המחיר האחרון הוא ₪{price:,.2f} ליחידה"
        if supplier:
            message += f" אצל {supplier}"
        if date:
            message += f", בתאריך {date}"
        message += "."
    else:
        message = f"{match_note}{product}: the latest price is ₪{price:,.2f} per unit"
        if supplier:
            message += f" from {supplier}"
        if date:
            message += f" on {date}"
        message += "."
    return {"route": "product", "understood": True, "message": message}


def _product_supplier_answer(question: str) -> dict[str, Any]:
    product, exact = _match_product(question)
    hebrew = _is_hebrew(question)
    if not product:
        message = (
            "לא מצאתי מוצר תואם בזיכרון העסקי."
            if hebrew else "I couldn't find a matching product in Business Memory."
        )
        return {"route": "supplier", "understood": True, "message": message}

    history = product_price_history(product)
    if history.empty:
        message = (
            f"אין עדיין היסטוריית ספקים עבור {product}."
            if hebrew else f"There is no supplier history for {product} yet."
        )
        return {"route": "supplier", "understood": True, "message": message}

    latest = history.iloc[-1]
    supplier = str(latest.get("supplier") or "").strip()
    date = str(latest.get("invoice_date") or "").strip()
    if not supplier:
        message = (
            f"לרכישה האחרונה של {product} לא שמור שם ספק."
            if hebrew else f"The latest {product} purchase has no stored supplier name."
        )
    elif hebrew:
        prefix = "ההתאמה הקרובה ביותר היא " if not exact else ""
        message = f"{prefix}{product}: הספק ברכישה האחרונה הוא {supplier}"
        message += f", בתאריך {date}." if date else "."
    else:
        prefix = "The closest stored match is " if not exact else ""
        message = f"{prefix}{product}: the latest supplier is {supplier}"
        message += f" on {date}." if date else "."
    return {"route": "supplier", "understood": True, "message": message}


def _monthly_spending_answer(question: str) -> dict[str, Any]:
    hebrew = _is_hebrew(question)
    month = datetime.now().strftime("%Y-%m")
    summary = month_summary(month)
    count = int(summary["documents_count"])
    total = float(summary["total"])
    if hebrew:
        message = f"החודש שמורים {count} מסמכים בסכום כולל של ₪{total:,.2f}."
    else:
        message = f"This month, {count} stored invoices total ₪{total:,.2f}."
    return {"route": "spending", "understood": True, "message": message}


def _largest_increase_answer(question: str) -> dict[str, Any]:
    hebrew = _is_hebrew(question)
    comparisons = []
    for description in _product_descriptions():
        summary = product_price_change_summary(description)
        change = summary.get("price_change_pct")
        if change is not None and change > 0:
            comparisons.append(summary)

    if not comparisons:
        message = (
            "אין לי עדיין מספיק היסטוריית מחירים כדי לזהות את ההתייקרות הגדולה ביותר."
            if hebrew else
            "I don't have enough price history yet to identify the largest increase."
        )
        return {"route": "product", "understood": True, "message": message}

    result = max(comparisons, key=lambda item: item["price_change_pct"])
    current = result["current_price"]
    previous = result["previous_price"]
    change = result["price_change_pct"]
    if hebrew:
        message = (
            f"{result['description']} התייקר הכי הרבה: מ־₪{previous:,.2f} "
            f"ל־₪{current:,.2f} ({change:+.1f}%)."
        )
    else:
        message = (
            f"{result['description']} increased the most: from ₪{previous:,.2f} "
            f"to ₪{current:,.2f} ({change:+.1f}%)."
        )
    return {"route": "product", "understood": True, "message": message}


def answer_business_question(question: str) -> dict[str, Any]:
    cleaned = " ".join(str(question or "").split())
    lowered = cleaned.casefold()
    if not cleaned:
        return {"route": "unknown", "understood": False, "message": ""}

    largest_increase = (
        ("increased" in lowered and "most" in lowered)
        or ("התייקר" in cleaned and "הכי" in cleaned)
    )
    if largest_increase:
        return _largest_increase_answer(cleaned)

    spending = any(term in lowered for term in ("spend", "spent", "הוצאתי", "הוצאות", "שילמתי"))
    this_month = any(term in lowered for term in ("this month", "החודש"))
    if spending and this_month:
        return _monthly_spending_answer(cleaned)

    supplier_question = any(
        term in lowered for term in ("who supplies", "supplier", "מי הספק", "ספק של")
    )
    if supplier_question:
        return _product_supplier_answer(cleaned)

    price_question = any(term in lowered for term in ("price", "מחיר"))
    if price_question:
        return _product_price_answer(cleaned)

    invoice_question = any(term in lowered for term in ("invoice", "invoices", "חשבונית", "חשבוניות"))
    if invoice_question:
        results = natural_language_query(cleaned)
        if not results.empty:
            return {
                "route": "invoice_search",
                "understood": True,
                "message": "",
                "results": results,
            }

    message = (
        "לא הבנתי את השאלה מספיק טוב. נסו לשאול על מוצר, ספק, הוצאה או חשבונית מסוימת."
        if _is_hebrew(cleaned) else
        "I couldn't understand that question clearly. Try asking about a product, supplier, spending period, or specific invoice."
    )
    return {"route": "unknown", "understood": False, "message": message}
