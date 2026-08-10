from __future__ import annotations

from enum import Enum
from typing import Any, Mapping


class SemanticLineType(str, Enum):
    """Small business-meaning taxonomy for extracted invoice charges."""

    PRODUCT = "product"
    SERVICE = "service"
    DELIVERY = "delivery"
    FEE = "fee"
    DISCOUNT_OR_ADJUSTMENT = "discount_or_adjustment"
    UNKNOWN = "unknown"


_DELIVERY_TERMS = (
    "הובלה",
    "משלוח",
    "דמי משלוח",
    "shipping",
    "delivery",
    "freight",
    "courier",
)
_SERVICE_TERMS = (
    "התקנה",
    "תיקון",
    "עבודת שירות",
    "שירות מקצועי",
    "ייעוץ",
    "installation",
    "repair",
    "labour",
    "labor",
    "professional service",
    "consulting",
)
_FEE_TERMS = (
    "דמי טיפול",
    "עמלה",
    "אגרה",
    "handling fee",
    "processing fee",
    "commission",
    "service fee",
)
_ADJUSTMENT_TERMS = (
    "הנחה",
    "זיכוי",
    "קיזוז",
    "התאמה",
    "discount",
    "rebate",
    "adjustment",
    "credit adjustment",
)
_PRODUCT_TERMS = (
    "מקרר",
    "מקפיא",
    "מפצל",
    "בקבוק",
    "ארגז",
    "חומר גלם",
    "refrigerator",
    "freezer",
    "bottle",
    "case",
    "ingredient",
)
_NON_ITEM_TERMS = (
    'סה"כ',
    "סהכ",
    "סך הכל",
    "לתשלום",
    'מע"מ',
    "מעמ",
    "vat",
    "total",
    "ויזה",
    "אשראי",
    "מאסטר",
    "מזומן",
    "כרטיס",
    "הערה",
    "remarks",
    "note",
)
_SUPPORTED_VALUES = {value.value for value in SemanticLineType}
_LEGACY_NON_PRODUCT_TYPES = {
    "discount": SemanticLineType.DISCOUNT_OR_ADJUSTMENT.value,
    "total": SemanticLineType.UNKNOWN.value,
    "vat": SemanticLineType.UNKNOWN.value,
    "payment": SemanticLineType.UNKNOWN.value,
    "note": SemanticLineType.UNKNOWN.value,
}


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def classify_invoice_line(
    description: str,
    *,
    quantity: Any = None,
    unit_price: Any = None,
    line_total: Any = None,
) -> str:
    """Classify one extracted charge without changing its financial meaning."""
    text = " ".join(str(description or "").strip().casefold().split())
    if not text:
        return SemanticLineType.UNKNOWN.value

    amounts = (_number(quantity), _number(unit_price), _number(line_total))
    if any(value is not None and value < 0 for value in amounts):
        return SemanticLineType.DISCOUNT_OR_ADJUSTMENT.value
    if any(term in text for term in _ADJUSTMENT_TERMS):
        return SemanticLineType.DISCOUNT_OR_ADJUSTMENT.value
    if any(term in text for term in _DELIVERY_TERMS):
        return SemanticLineType.DELIVERY.value
    if any(term in text for term in _FEE_TERMS):
        return SemanticLineType.FEE.value
    if any(term in text for term in _SERVICE_TERMS):
        return SemanticLineType.SERVICE.value
    if any(term in text for term in _NON_ITEM_TERMS):
        return SemanticLineType.UNKNOWN.value

    if any(term in text for term in _PRODUCT_TERMS):
        return SemanticLineType.PRODUCT.value
    if any(value is not None for value in amounts):
        # A priced/quantified extracted item row is usable product evidence once
        # deterministic non-product wording above has been ruled out.
        return SemanticLineType.PRODUCT.value
    return SemanticLineType.UNKNOWN.value


def classify_invoice_item(item: Mapping[str, Any]) -> str:
    """Resolve new and legacy item records through the same semantic contract."""
    classified = classify_invoice_line(
        str(item.get("description") or ""),
        quantity=item.get("quantity"),
        unit_price=item.get("unit_price"),
        line_total=item.get("line_total"),
    )
    stored = str(item.get("line_type") or "").strip().casefold()

    # Deterministic evidence always protects memory from a legacy false product.
    if classified != SemanticLineType.PRODUCT.value:
        return classified
    if stored in _SUPPORTED_VALUES and stored != SemanticLineType.PRODUCT.value:
        return stored
    if stored in _LEGACY_NON_PRODUCT_TYPES:
        return _LEGACY_NON_PRODUCT_TYPES[stored]
    return classified


def is_product_line(item: Mapping[str, Any]) -> bool:
    return classify_invoice_item(item) == SemanticLineType.PRODUCT.value
