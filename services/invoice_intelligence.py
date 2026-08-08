from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
import re
from statistics import median
from typing import Any, Iterable, Mapping, Protocol, Sequence


class Severity:
    INFO = "info"
    POSITIVE = "positive"
    ATTENTION = "attention"
    WARNING = "warning"


class Category:
    SUPPLIER = "supplier"
    PRODUCT = "product"
    PRICE = "price"
    DUPLICATE = "duplicate"
    COMPLETENESS = "completeness"
    SPEND = "spend"
    TAX = "tax"
    LEARNING = "learning"
    BEHAVIOR = "behavior"


@dataclass(frozen=True)
class Insight:
    title: str
    description: str
    severity: str
    category: str
    confidence: float
    explanation: str = ""
    icon: str = "•"
    priority: int = field(default=0, repr=False, compare=False)
    evidence: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
    source_record_ids: tuple[int | str, ...] = field(default_factory=tuple)
    recommended_next_action: str | None = None
    proactive: bool = field(default=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.explanation:
            object.__setattr__(self, "explanation", self.description)


@dataclass(frozen=True)
class InvoiceIntelligenceContext:
    invoice: Mapping[str, Any]
    invoices: Sequence[Mapping[str, Any]] = ()
    items: Sequence[Mapping[str, Any]] = ()
    price_histories: Mapping[str, Sequence[Mapping[str, Any]]] = field(default_factory=dict)
    validations: Mapping[str, Any] = field(default_factory=dict)


class InsightRule(Protocol):
    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]: ...


def _text(value: Any) -> str:
    return str(value or "").strip()


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if number != number else number


def _date(value: Any) -> datetime | None:
    cleaned = _text(value)
    if not cleaned:
        return None
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def _money(value: float) -> str:
    return f"₪{value:,.2f}"


def _is_before(record: Mapping[str, Any], current: Mapping[str, Any]) -> bool:
    record_id = int(record.get("id") or record.get("invoice_id") or 0)
    current_id = int(current.get("id") or 0)
    record_date = _date(record.get("invoice_date"))
    current_date = _date(current.get("invoice_date"))
    if record_date is None or current_date is None:
        return record_id < current_id
    return record_date < current_date or (
        record_date == current_date and record_id < current_id
    )


def _same_supplier(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_canonical = left.get("canonical_supplier_id")
    right_canonical = right.get("canonical_supplier_id")
    if left_canonical and right_canonical:
        return int(left_canonical) == int(right_canonical)
    left_id, right_id = _text(left.get("supplier_id")), _text(right.get("supplier_id"))
    if left_id and right_id:
        return left_id == right_id
    return bool(_text(left.get("supplier"))) and _text(left.get("supplier")) == _text(right.get("supplier"))


def _source_record_id(record: Mapping[str, Any]) -> int | str | None:
    value = record.get("source_record_id") or record.get("id") or record.get("invoice_id")
    if value in (None, "", 0, "0"):
        return None
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return str(value)
    return numeric if numeric > 0 else None


def _record_ids(
    records: Iterable[Mapping[str, Any]],
    current: Mapping[str, Any] | None = None,
) -> tuple[int | str, ...]:
    values = [_source_record_id(record) for record in records]
    if current is not None:
        values.append(_source_record_id(current))
    return tuple(dict.fromkeys(value for value in values if value is not None))


def _history_matches_supplier(
    history_row: Mapping[str, Any],
    current: Mapping[str, Any],
    invoices: Sequence[Mapping[str, Any]],
) -> bool:
    invoice_id = int(history_row.get("invoice_id") or history_row.get("id") or 0)
    source = next(
        (record for record in invoices if int(record.get("id") or 0) == invoice_id),
        None,
    )
    if source is not None:
        return _same_supplier(source, current)
    return _text(history_row.get("supplier")) == _text(current.get("supplier"))


def _comparable_unit(record: Mapping[str, Any]) -> str:
    return _text(record.get("normalized_unit") or record.get("unit")).casefold()


def _supplier_name(record: Mapping[str, Any]) -> str:
    return _text(record.get("canonical_supplier_name") or record.get("supplier"))


def _product_name(record: Mapping[str, Any]) -> str:
    return _text(record.get("canonical_product_name") or record.get("description"))


def _same_packaging(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_quantity = _number(left.get("package_quantity"))
    right_quantity = _number(right.get("package_quantity"))
    left_unit = _text(left.get("package_unit")).casefold()
    right_unit = _text(right.get("package_unit")).casefold()
    if left_quantity is None and right_quantity is None:
        return True
    return (
        left_quantity is not None
        and right_quantity is not None
        and abs(left_quantity - right_quantity) < 1e-9
        and left_unit == right_unit
    )


def _trusted_fact_price(record: Mapping[str, Any]) -> float | None:
    if _text(record.get("fact_status")) != "TRUSTED":
        return None
    return _number(record.get("normalized_price"))


class MissingInvoiceNumberRule:
    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]:
        if not _text(context.invoice.get("invoice_number")):
            yield Insight(
                title="Missing Invoice Number",
                description="I need your help with the invoice number.",
                severity=Severity.ATTENTION,
                category=Category.COMPLETENESS,
                confidence=1.0,
                icon="🔎",
                priority=100,
            )


class DuplicateInvoiceRule:
    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]:
        current = context.invoice
        number = _text(current.get("invoice_number"))
        document_type = _text(current.get("document_type"))
        if not number:
            return
        matches = [
            row for row in context.invoices
            if int(row.get("id") or 0) != int(current.get("id") or 0)
            and _same_supplier(row, current)
            and _text(row.get("invoice_number")) == number
            and _text(row.get("document_type")) == document_type
        ]
        if matches:
            yield Insight(
                title="Possible Duplicate",
                description="I've seen another invoice with the same supplier, number, and document type.",
                severity=Severity.WARNING,
                category=Category.DUPLICATE,
                confidence=0.99,
                icon="🗂️",
                priority=95,
                evidence={"matching_invoice_ids": [row.get("id") for row in matches]},
                source_record_ids=_record_ids(matches, current),
                recommended_next_action="Compare the invoices before deciding whether to keep both.",
                proactive=True,
            )


class NearDuplicateInvoiceRule:
    @staticmethod
    def _number_parts(value: Any) -> tuple[str, ...]:
        return tuple(sorted(part for part in re.split(r"[^0-9A-Za-z]+", _text(value).casefold()) if part))

    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]:
        current = context.invoice
        current_number = _text(current.get("invoice_number"))
        current_parts = self._number_parts(current_number)
        current_date = _text(current.get("invoice_date"))
        current_total = _number(current.get("total"))
        document_type = _text(current.get("document_type"))
        if len(current_parts) < 2 or not current_date or current_total is None or current_total <= 0:
            return
        matches = []
        for row in context.invoices:
            if int(row.get("id") or 0) == int(current.get("id") or 0):
                continue
            other_number = _text(row.get("invoice_number"))
            other_total = _number(row.get("total"))
            if (
                other_number != current_number
                and self._number_parts(other_number) == current_parts
                and _same_supplier(row, current)
                and _text(row.get("document_type")) == document_type
                and _text(row.get("invoice_date")) == current_date
                and other_total is not None
                and abs(other_total - current_total) <= 0.01
            ):
                matches.append(row)
        if not matches:
            return
        yield Insight(
            title="Possible Similar Invoice",
            description=(
                "I've seen a very similar invoice with the same supplier, date, total, "
                "and invoice-number parts."
            ),
            severity=Severity.WARNING,
            category=Category.DUPLICATE,
            confidence=0.95,
            icon="🗂️",
            priority=90,
            evidence={
                "current_invoice_number": current_number,
                "matching_invoice_numbers": [row.get("invoice_number") for row in matches],
                "invoice_date": current_date,
                "total": current_total,
            },
            source_record_ids=_record_ids(matches, current),
            recommended_next_action="Compare the invoices before deciding whether both belong in Business Memory.",
            proactive=True,
        )


class SupplierHistoryRule:
    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]:
        current = context.invoice
        supplier = _supplier_name(current)
        if not supplier:
            return
        current_id = int(current.get("id") or 0)
        previous = [
            row for row in context.invoices
            if _same_supplier(row, current)
            and int(row.get("id") or 0) != current_id
            and (not current_id or int(row.get("id") or 0) < current_id)
        ]
        if not previous:
            yield Insight(
                title="First Supplier Invoice",
                description=f"This is the first invoice Barni remembers from {supplier}.",
                severity=Severity.POSITIVE,
                category=Category.SUPPLIER,
                confidence=1.0,
                icon="✨",
                priority=70,
                evidence={"supplier": supplier, "previous_invoice_count": 0},
                source_record_ids=_record_ids((), current),
                proactive=True,
            )


class UnusualInvoiceTotalRule:
    minimum_history = 3
    minimum_change_pct = 50.0
    minimum_amount_change = 100.0

    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]:
        current = context.invoice
        current_total = _number(current.get("total"))
        if current_total is None or current_total <= 0:
            return
        document_type = _text(current.get("document_type"))
        previous = [
            row for row in context.invoices
            if _same_supplier(row, current)
            and _is_before(row, current)
            and _text(row.get("document_type")) == document_type
            and ((_number(row.get("total")) or 0) > 0)
        ]
        previous.sort(key=lambda row: (_date(row.get("invoice_date")) or datetime.min, int(row.get("id") or 0)))
        previous = previous[-6:]
        if len(previous) < self.minimum_history:
            return
        previous_totals = [_number(row.get("total")) for row in previous]
        typical = float(median(previous_totals))
        if typical <= 0:
            return
        change = (current_total - typical) / typical * 100
        if abs(change) < self.minimum_change_pct or abs(current_total - typical) < self.minimum_amount_change:
            return
        direction = "higher" if change > 0 else "lower"
        supplier = _supplier_name(current) or "this supplier"
        yield Insight(
            title="Unusual Invoice Total",
            description=f"This invoice is {abs(change):.0f}% {direction} than the typical {supplier} invoice ({_money(typical)}).",
            severity=Severity.ATTENTION,
            category=Category.SPEND,
            confidence=0.9,
            icon="↕",
            priority=85,
            evidence={
                "current_total": current_total,
                "typical_total": typical,
                "change_pct": round(change, 2),
                "comparison_count": len(previous_totals),
            },
            source_record_ids=_record_ids(previous, current),
            recommended_next_action="Review the total against the recent invoices from this supplier.",
            proactive=True,
        )


class ProductKnowledgeRule:
    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]:
        current_id = int(context.invoice.get("id") or 0)
        new_products: list[str] = []
        for item in context.items:
            description = _product_name(item)
            if not description or _text(item.get("line_type") or "product") != "product":
                continue
            if _number(item.get("quantity")) is None or _number(item.get("unit_price")) is None:
                continue
            history = context.price_histories.get(description, ())
            previous = [row for row in history if int(row.get("invoice_id") or 0) != current_id and _is_before(row, context.invoice)]
            if not previous:
                new_products.append(description)
        new_products = list(dict.fromkeys(new_products))
        if not new_products:
            return
        if len(new_products) == 1:
            description = f"{new_products[0]} appears in Business Memory for the first time."
            title = "New Product"
        else:
            description = f"Barni learned {len(new_products)} products from this invoice for the first time."
            title = "New Products"
        yield Insight(
            title=title,
            description=description,
            severity=Severity.POSITIVE,
            category=Category.PRODUCT,
            confidence=0.95,
            icon="🌱",
            priority=55,
            evidence={"products": new_products},
            source_record_ids=_record_ids((), context.invoice),
        )


class SupplierProductNoveltyRule:
    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]:
        current = context.invoice
        supplier = _supplier_name(current)
        previous_supplier_invoices = [
            row for row in context.invoices
            if _same_supplier(row, current) and _is_before(row, current)
        ]
        if not supplier or not previous_supplier_invoices:
            return

        products: list[str] = []
        evidence_rows: list[Mapping[str, Any]] = []
        current_id = int(current.get("id") or 0)
        for item in context.items:
            description = _product_name(item)
            if not description or _text(item.get("line_type") or "product") != "product":
                continue
            history = [
                row for row in context.price_histories.get(description, ())
                if int(row.get("invoice_id") or 0) != current_id and _is_before(row, current)
            ]
            if not history:
                continue
            supplier_history = [
                row for row in history
                if _history_matches_supplier(row, current, context.invoices)
            ]
            if not supplier_history:
                products.append(description)
                evidence_rows.extend(history[-1:])

        products = list(dict.fromkeys(products))
        if not products:
            return
        if len(products) == 1:
            explanation = f"This is the first time {supplier} has sold you {products[0]}."
            title = "New Product From This Supplier"
        else:
            explanation = f"This is the first time {supplier} has sold you {len(products)} products on this invoice."
            title = "New Products From This Supplier"
        yield Insight(
            title=title,
            description=explanation,
            severity=Severity.INFO,
            category=Category.PRODUCT,
            confidence=0.95,
            icon="🌱",
            priority=72,
            evidence={
                "supplier": supplier,
                "products": products,
                "previous_supplier_invoice_count": len(previous_supplier_invoices),
            },
            source_record_ids=_record_ids([*previous_supplier_invoices, *evidence_rows], current),
            proactive=True,
        )


class RepeatedPriceIncreaseRule:
    minimum_step_pct = 2.0
    minimum_total_pct = 8.0

    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]:
        current = context.invoice
        current_id = int(current.get("id") or 0)
        supplier = _supplier_name(current)
        for item in context.items:
            description = _product_name(item)
            current_price = _trusted_fact_price(item)
            if not description or current_price is None or current_price <= 0:
                continue
            previous = [
                row for row in context.price_histories.get(description, ())
                if int(row.get("invoice_id") or 0) != current_id
                and _history_matches_supplier(row, current, context.invoices)
                and _is_before(row, current)
                and ((_trusted_fact_price(row) or 0) > 0)
            ]
            previous.sort(key=lambda row: (_date(row.get("invoice_date")) or datetime.min, int(row.get("invoice_id") or 0)))
            if len(previous) < 2:
                continue
            comparison = previous[-2:]
            prices = [_trusted_fact_price(row) for row in comparison] + [current_price]
            basis = _text(item.get("normalized_unit"))
            price_basis = f" per {basis}" if basis else ""
            step_changes = [
                (prices[index] - prices[index - 1]) / prices[index - 1] * 100
                for index in range(1, len(prices))
            ]
            total_change = (prices[-1] - prices[0]) / prices[0] * 100
            if any(change < self.minimum_step_pct for change in step_changes) or total_change < self.minimum_total_pct:
                continue
            yield Insight(
                title="Repeated Price Increase",
                description=(
                    f"{description} increased again. Its price rose across the last three "
                    f"purchases, from {_money(prices[0])} to {_money(prices[-1])}{price_basis} "
                    f"(+{total_change:.1f}%)."
                ),
                severity=Severity.ATTENTION,
                category=Category.PRICE,
                confidence=0.99,
                icon="📈",
                priority=92 + min(int(total_change // 10), 5),
                evidence={
                    "product": description,
                    "prices": prices,
                    "step_changes_pct": [round(value, 2) for value in step_changes],
                    "total_change_pct": round(total_change, 2),
                },
                source_record_ids=_record_ids(comparison, current),
                recommended_next_action="Review the latest price with this supplier.",
                proactive=True,
            )


class PriceMovementRule:
    minimum_change_pct = 5.0

    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]:
        current = context.invoice
        current_id = int(current.get("id") or 0)
        supplier = _supplier_name(current)
        movements: list[Insight] = []
        for item in context.items:
            description = _product_name(item)
            current_price = _trusted_fact_price(item)
            if not description or current_price is None or current_price <= 0:
                continue
            comparable = [
                row for row in context.price_histories.get(description, ())
                if int(row.get("invoice_id") or 0) != current_id
                and _history_matches_supplier(row, current, context.invoices)
                and _is_before(row, current)
                and (_trusted_fact_price(row) or 0) > 0
            ]
            if not comparable:
                continue
            comparable.sort(key=lambda row: (_date(row.get("invoice_date")) or datetime.min, int(row.get("invoice_id") or 0)))
            previous_price = _trusted_fact_price(comparable[-1])
            if previous_price is None or previous_price <= 0:
                continue
            change = (current_price - previous_price) / previous_price * 100
            if abs(change) < self.minimum_change_pct:
                continue
            increased = change > 0
            quantity = _number(item.get("quantity"))
            package_quantity = _number(item.get("package_quantity"))
            estimated_impact = (
                (current_price - previous_price) * quantity * package_quantity
                if quantity is not None and quantity > 0
                and package_quantity is not None and package_quantity > 0
                else None
            )
            is_significant = abs(change) >= 10.0
            basis = _text(item.get("normalized_unit"))
            price_basis = f" per {basis}" if basis else ""
            movements.append(Insight(
                title="Price Increase" if increased else "Price Decrease",
                description=(
                    f"{description} {'increased' if increased else 'decreased'} from "
                    f"{_money(previous_price)} to {_money(current_price)}{price_basis} since the previous "
                    f"purchase ({'+' if increased else ''}{change:.1f}%)."
                ),
                severity=Severity.ATTENTION if increased else Severity.POSITIVE,
                category=Category.PRICE,
                confidence=0.98,
                icon="📈" if increased else "📉",
                priority=(75 if increased else 65) + min(int(abs(change)), 15),
                evidence={
                    "product": description,
                    "previous_price": previous_price,
                    "current_price": current_price,
                    "change_pct": round(change, 2),
                    "estimated_line_impact": estimated_impact,
                },
                source_record_ids=_record_ids(comparable[-1:], current),
                recommended_next_action=(
                    "Review this price change before approving the invoice."
                    if is_significant else None
                ),
                proactive=is_significant,
            ))
        yield from sorted(movements, key=lambda insight: insight.priority, reverse=True)[:2]


class RecurringPurchaseRule:
    minimum_purchase_dates = 5

    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]:
        current = context.invoice
        current_id = int(current.get("id") or 0)
        supplier = _supplier_name(current)
        current_date = _date(current.get("invoice_date"))
        if not supplier or current_date is None:
            return
        for item in context.items:
            description = _product_name(item)
            if not description:
                continue
            history = [
                row for row in context.price_histories.get(description, ())
                if int(row.get("invoice_id") or 0) != current_id
                and _history_matches_supplier(row, current, context.invoices)
                and _is_before(row, current)
                and _date(row.get("invoice_date")) is not None
                and _same_packaging(row, item)
            ]
            dated_rows: dict[datetime, Mapping[str, Any]] = {
                _date(row.get("invoice_date")): row for row in history
            }
            dated_rows[current_date] = current
            dates = sorted(dated_rows)
            if len(dates) < self.minimum_purchase_dates:
                continue
            dates = dates[-self.minimum_purchase_dates:]
            intervals = [(dates[index] - dates[index - 1]).days for index in range(1, len(dates))]
            typical = float(median(intervals))
            if typical < 3 or typical > 31:
                continue
            tolerance = max(2.0, typical * 0.30)
            consistent = sum(abs(interval - typical) <= tolerance for interval in intervals)
            if consistent < 3:
                continue
            lower = max(1, round(typical - tolerance))
            upper = round(typical + tolerance)
            source_rows = [dated_rows[value] for value in dates]
            yield Insight(
                title="Recurring Purchase Pattern",
                description=f"You usually buy {description} from {supplier} every {lower}–{upper} days.",
                severity=Severity.INFO,
                category=Category.BEHAVIOR,
                confidence=0.90,
                icon="↻",
                priority=68,
                evidence={
                    "product": description,
                    "supplier": supplier,
                    "intervals_days": intervals,
                    "typical_interval_days": typical,
                    "purchase_count": len(dates),
                },
                source_record_ids=_record_ids(source_rows),
                proactive=True,
            )


class VatValidationRule:
    def evaluate(self, context: InvoiceIntelligenceContext) -> Iterable[Insight]:
        warning = context.validations.get("vat_warning")
        if not warning:
            return
        description = warning if isinstance(warning, str) else "The stored VAT validation needs your attention."
        yield Insight(
            title="VAT Needs Attention",
            description=description,
            severity=Severity.ATTENTION,
            category=Category.TAX,
            confidence=1.0,
            icon="◌",
            priority=90,
        )


class InvoiceIntelligenceEngine:
    def __init__(self, rules: Sequence[InsightRule] | None = None, max_insights: int = 3):
        self.rules = tuple(rules or DEFAULT_RULES)
        self.max_insights = max_insights

    def analyze(self, context: InvoiceIntelligenceContext) -> list[Insight]:
        insights = [insight for rule in self.rules for insight in rule.evaluate(context)]
        current_source = _source_record_id(context.invoice)
        if current_source is not None:
            insights = [
                insight
                if insight.source_record_ids
                else replace(insight, source_record_ids=(current_source,))
                for insight in insights
            ]
        insights.sort(key=lambda insight: (insight.priority, insight.confidence), reverse=True)
        return insights[: self.max_insights]


DEFAULT_RULES: tuple[InsightRule, ...] = (
    MissingInvoiceNumberRule(),
    DuplicateInvoiceRule(),
    NearDuplicateInvoiceRule(),
    VatValidationRule(),
    UnusualInvoiceTotalRule(),
    RepeatedPriceIncreaseRule(),
    PriceMovementRule(),
    SupplierHistoryRule(),
    SupplierProductNoveltyRule(),
    ProductKnowledgeRule(),
    RecurringPurchaseRule(),
)


def analyze_invoice(
    context: InvoiceIntelligenceContext,
    *,
    rules: Sequence[InsightRule] | None = None,
    max_insights: int = 3,
) -> list[Insight]:
    return InvoiceIntelligenceEngine(rules=rules, max_insights=max_insights).analyze(context)


def select_proactive_insights(
    insights: Sequence[Insight],
    *,
    max_insights: int = 3,
) -> list[Insight]:
    strong = [insight for insight in insights if insight.proactive and insight.priority >= 65]
    strong.sort(key=lambda insight: (insight.priority, insight.confidence), reverse=True)
    repeated_products = {
        insight.evidence.get("product")
        for insight in strong
        if insight.title == "Repeated Price Increase"
    }
    has_duplicate = any(insight.category == Category.DUPLICATE for insight in strong)
    deduplicated = [
        insight
        for insight in strong
        if not (
            insight.title == "Price Increase"
            and insight.evidence.get("product") in repeated_products
        )
        and not (has_duplicate and insight.title == "First Supplier Invoice")
    ]
    return deduplicated[:max_insights]
