from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Mapping, Protocol, Sequence

from database import connect
from services.business_identity import (
    BusinessIdentityRepository,
    normalize_currency,
    normalize_packaging,
    normalize_unit,
)


class FactStatus:
    TRUSTED = "TRUSTED"
    PARTIALLY_TRUSTED = "PARTIALLY TRUSTED"
    INSUFFICIENT_DATA = "INSUFFICIENT DATA"
    IDENTITY_CONFLICT = "IDENTITY CONFLICT"
    UNIT_CONFLICT = "UNIT CONFLICT"
    PACKAGE_CONFLICT = "PACKAGE CONFLICT"
    VAT_CONFLICT = "VAT CONFLICT"
    CURRENCY_CONFLICT = "CURRENCY CONFLICT"
    NOT_COMPARABLE = "NOT COMPARABLE"


@dataclass(frozen=True)
class BusinessFact:
    id: int | None
    fact_type: str
    fingerprint: str
    source_type: str
    source_record_id: int
    trust_status: str
    business_confidence: float
    status_explanation: str
    confidence: Mapping[str, float]
    evidence: Mapping[str, Any]
    payload: Mapping[str, Any]
    observed_at: str


@dataclass(frozen=True)
class ComparablePriceFact:
    fact: BusinessFact
    canonical_product_id: int | None
    canonical_product_name: str
    canonical_supplier_id: int | None
    canonical_supplier_name: str
    invoice_id: int
    invoice_item_id: int
    observed_price: float | None
    normalized_price: float | None
    normalized_unit: str
    package_quantity: float | None
    package_unit: str
    quantity: float | None
    vat_basis: str
    currency: str
    observation_date: str
    document_type: str
    is_credit: bool

    @property
    def trusted(self) -> bool:
        return self.fact.trust_status == FactStatus.TRUSTED

    def as_record(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact.id,
            "fact_status": self.fact.trust_status,
            "business_confidence": self.fact.business_confidence,
            "status_explanation": self.fact.status_explanation,
            "canonical_product_id": self.canonical_product_id,
            "canonical_product_name": self.canonical_product_name,
            "canonical_supplier_id": self.canonical_supplier_id,
            "canonical_supplier_name": self.canonical_supplier_name,
            "invoice_id": self.invoice_id,
            "item_id": self.invoice_item_id,
            "unit_price": self.observed_price,
            "observed_price": self.observed_price,
            "normalized_price": self.normalized_price,
            "normalized_unit": self.normalized_unit,
            "package_quantity": self.package_quantity,
            "package_unit": self.package_unit,
            "quantity": self.quantity,
            "vat_basis": self.vat_basis,
            "currency": self.currency,
            "invoice_date": self.observation_date,
            "document_type": self.document_type,
            "is_credit": self.is_credit,
            "source_record_ids": tuple(self.fact.evidence.get("invoice_ids", ())),
        }


@dataclass(frozen=True)
class PriceComparison:
    current: ComparablePriceFact
    previous: ComparablePriceFact
    comparable: bool
    status: str
    explanation: str
    change_amount: float | None = None
    change_pct: float | None = None
    evidence_invoice_ids: tuple[int, ...] = ()


class FactBuilder(Protocol):
    fact_type: str

    def build(self, row: Mapping[str, Any]) -> BusinessFact: ...


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if number != number else number


def _text(value: Any) -> str:
    return str(value or "").strip()


def _credit_document(document_type: Any, total: Any) -> bool:
    value = _text(document_type).casefold()
    return "credit" in value or "זיכוי" in value or ((_number(total) or 0) < 0)


def _close(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return False
    return abs(left - right) <= max(1.0, abs(right) * 0.01)


def _vat_basis(row: Mapping[str, Any]) -> tuple[str, str | None]:
    subtotal = _number(row.get("subtotal"))
    vat = _number(row.get("vat"))
    total = _number(row.get("invoice_total", row.get("total")))
    treatment = _text(row.get("tax_treatment")).casefold()
    if "פטור" in treatment and (vat is None or abs(vat) <= 0.01):
        return "EXEMPT", None
    if "חייב" in treatment and (vat is None or abs(vat) <= 0.01):
        return "", "The invoice is marked as taxable but has no supported VAT amount."
    if subtotal is not None and total is not None and vat is not None:
        if abs(vat) <= 0.01 and _close(subtotal, total):
            return "EXEMPT", None
        if _close(subtotal + vat, total):
            return "EXCLUSIVE", None
        if vat > 0 and _close(subtotal, total):
            return "INCLUSIVE", None
        return "", "The invoice totals do not establish a consistent VAT basis."
    if vat is not None and abs(vat) <= 0.01 and subtotal is not None and _close(subtotal, total):
        return "EXEMPT", None
    return "", "The VAT basis is not supported by complete invoice totals."


_BASE_UNITS = {
    "kg": ("kg", 1.0), "g": ("kg", 0.001),
    "l": ("l", 1.0), "ml": ("l", 0.001),
    "unit": ("unit", 1.0),
}


class ComparablePriceFactBuilder:
    fact_type = "comparable_price"

    def build(self, row: Mapping[str, Any]) -> BusinessFact:
        item_id = int(row["invoice_item_id"])
        invoice_id = int(row["invoice_id"])
        observed_price = _number(row.get("unit_price"))
        quantity = _number(row.get("quantity"))
        raw_unit = normalize_unit(row.get("unit"))
        packaging = normalize_packaging(row.get("description"), row.get("unit"))
        currency = normalize_currency(row.get("currency"))
        vat_basis, vat_problem = _vat_basis(row)
        is_credit = _credit_document(row.get("document_type"), row.get("invoice_total"))
        product_id = row.get("canonical_product_id")
        supplier_id = row.get("canonical_supplier_id")

        confidence = {
            "supplier_identity": 1.0 if supplier_id else 0.0,
            "product_identity": 1.0 if product_id else 0.0,
            "unit": 0.0,
            "package": 0.0,
            "currency": 1.0 if currency in {"ILS", "USD", "EUR", "GBP"} else 0.0,
            "vat": 1.0 if vat_basis else 0.0,
            "quantity": 1.0 if quantity is not None and quantity > 0 else 0.0,
            "source_evidence": 1.0 if invoice_id and item_id else 0.0,
        }
        status = FactStatus.TRUSTED
        reason = "This price has a complete, comparable business basis."
        normalized_unit = ""
        normalized_price = None
        package_quantity: float | None = None
        package_unit = ""

        if is_credit:
            status = FactStatus.NOT_COMPARABLE
            reason = "Credit notes are adjustments, not purchase-price observations."
        elif not product_id or not supplier_id:
            status = FactStatus.IDENTITY_CONFLICT
            reason = "A canonical supplier or product identity is missing."
        elif observed_price is None or observed_price <= 0 or quantity is None or quantity <= 0:
            status = FactStatus.INSUFFICIENT_DATA
            reason = "A positive observed price and quantity are required."
        elif raw_unit not in {*_BASE_UNITS, "package"}:
            status = FactStatus.UNIT_CONFLICT
            reason = "The invoice unit is unknown, so Barni cannot establish a price basis."
        else:
            if raw_unit in {"kg", "g", "l", "ml"}:
                normalized_unit, factor = _BASE_UNITS[raw_unit]
                package_quantity = factor
                package_unit = normalized_unit
                normalized_price = observed_price / factor
                confidence["unit"] = 1.0
                confidence["package"] = 1.0
            elif packaging.quantity is not None and packaging.unit in _BASE_UNITS:
                normalized_unit, factor = _BASE_UNITS[packaging.unit]
                package_quantity = packaging.quantity * factor
                package_unit = normalized_unit
                if package_quantity > 0:
                    normalized_price = observed_price / package_quantity
                    confidence["unit"] = 1.0
                    confidence["package"] = 1.0
            elif raw_unit == "unit":
                normalized_unit, package_quantity, package_unit = "unit", 1.0, "unit"
                normalized_price = observed_price
                confidence["unit"] = 1.0
                confidence["package"] = 1.0
            else:
                status = FactStatus.PACKAGE_CONFLICT
                reason = "The package size is missing, so a package price cannot be normalized."

        if status == FactStatus.TRUSTED and not confidence["currency"]:
            status = FactStatus.CURRENCY_CONFLICT
            reason = "The invoice currency is missing or unsupported."
        if status == FactStatus.TRUSTED and vat_problem:
            status = FactStatus.VAT_CONFLICT
            reason = vat_problem
        if status == FactStatus.TRUSTED and normalized_price is None:
            status = FactStatus.NOT_COMPARABLE
            reason = "A normalized price could not be established."

        business_confidence = sum(confidence.values()) / len(confidence)
        evidence = {
            "invoice_ids": [invoice_id],
            "invoice_item_ids": [item_id],
            "archived_path": _text(row.get("archived_path")),
            "observed_values": {
                "description": _text(row.get("description")),
                "unit": _text(row.get("unit")),
                "unit_price": observed_price,
                "quantity": quantity,
                "currency": _text(row.get("currency")),
                "subtotal": _number(row.get("subtotal")),
                "vat": _number(row.get("vat")),
                "total": _number(row.get("invoice_total")),
            },
        }
        payload = {
            "canonical_product_id": product_id,
            "canonical_supplier_id": supplier_id,
            "invoice_id": invoice_id,
            "invoice_item_id": item_id,
            "observed_price": observed_price,
            "normalized_price": normalized_price,
            "normalized_unit": normalized_unit,
            "package_quantity": package_quantity,
            "package_unit": package_unit,
            "quantity": quantity,
            "vat_basis": vat_basis,
            "currency": currency,
            "document_type": _text(row.get("document_type")),
            "is_credit": is_credit,
        }
        return BusinessFact(
            id=None,
            fact_type=self.fact_type,
            fingerprint=hashlib.sha256(f"price:invoice_item:{item_id}".encode()).hexdigest(),
            source_type="invoice_item",
            source_record_id=item_id,
            trust_status=status,
            business_confidence=business_confidence,
            status_explanation=reason,
            confidence=confidence,
            evidence=evidence,
            payload=payload,
            observed_at=_text(row.get("invoice_date")),
        )


class BusinessFactsEngine:
    """Materializes typed, evidence-bound facts for every registered fact builder."""

    def __init__(
        self,
        connection_factory: Callable[[], sqlite3.Connection] = connect,
        builders: Sequence[FactBuilder] | None = None,
    ) -> None:
        self._connect = connection_factory
        self.builders = tuple(builders or (ComparablePriceFactBuilder(),))
        self.identities = BusinessIdentityRepository(connection_factory)

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def sync(self) -> dict[str, int]:
        self.identities.sync_existing_memory()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT items.id invoice_item_id, items.invoice_id,
                       items.description, items.quantity, items.unit, items.unit_price,
                       items.line_total, items.line_type,
                       invoices.invoice_date, invoices.document_type,
                       invoices.currency, invoices.subtotal, invoices.vat,
                       invoices.total invoice_total, invoices.tax_treatment,
                       invoices.archived_path,
                       item_links.canonical_product_id,
                       invoice_links.canonical_supplier_id
                FROM invoice_items items
                JOIN invoices ON invoices.id = items.invoice_id
                LEFT JOIN invoice_item_identity_links item_links ON item_links.item_id = items.id
                LEFT JOIN invoice_identity_links invoice_links ON invoice_links.invoice_id = invoices.id
                WHERE items.line_type = 'product'
                ORDER BY items.id
                """
            ).fetchall()
            built = 0
            statuses: dict[str, int] = {}
            conflicts: list[BusinessFact] = []
            now = self._now()
            for source in rows:
                source_data = dict(source)
                for builder in self.builders:
                    fact = builder.build(source_data)
                    fact_id = self._upsert_fact(connection, fact, now)
                    if fact.fact_type == "comparable_price":
                        self._upsert_price(connection, fact_id, fact)
                    built += 1
                    statuses[fact.trust_status] = statuses.get(fact.trust_status, 0) + 1
                    if fact.trust_status in {
                        FactStatus.IDENTITY_CONFLICT, FactStatus.UNIT_CONFLICT,
                        FactStatus.PACKAGE_CONFLICT, FactStatus.VAT_CONFLICT,
                        FactStatus.CURRENCY_CONFLICT,
                    }:
                        conflicts.append(fact)
            connection.commit()
        self._enqueue_conflicts(conflicts)
        return {"facts": built, **statuses}

    def _upsert_fact(self, connection: sqlite3.Connection, fact: BusinessFact, now: str) -> int:
        connection.execute(
            """INSERT INTO business_facts(
                   fact_type, fingerprint, source_type, source_record_id,
                   trust_status, business_confidence, status_explanation,
                   confidence_json, evidence_json, payload_json, observed_at,
                   created_at, updated_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(fingerprint) DO UPDATE SET
                   trust_status = excluded.trust_status,
                   business_confidence = excluded.business_confidence,
                   status_explanation = excluded.status_explanation,
                   confidence_json = excluded.confidence_json,
                   evidence_json = excluded.evidence_json,
                   payload_json = excluded.payload_json,
                   observed_at = excluded.observed_at,
                   updated_at = excluded.updated_at""",
            (
                fact.fact_type, fact.fingerprint, fact.source_type, fact.source_record_id,
                fact.trust_status, fact.business_confidence, fact.status_explanation,
                json.dumps(dict(fact.confidence), ensure_ascii=False),
                json.dumps(dict(fact.evidence), ensure_ascii=False),
                json.dumps(dict(fact.payload), ensure_ascii=False), fact.observed_at, now, now,
            ),
        )
        return int(connection.execute("SELECT id FROM business_facts WHERE fingerprint = ?", (fact.fingerprint,)).fetchone()[0])

    @staticmethod
    def _upsert_price(connection: sqlite3.Connection, fact_id: int, fact: BusinessFact) -> None:
        value = fact.payload
        connection.execute(
            """INSERT INTO comparable_price_facts(
                   fact_id, canonical_product_id, canonical_supplier_id,
                   invoice_id, invoice_item_id, observed_price, normalized_price,
                   normalized_unit, package_quantity, package_unit, quantity,
                   vat_basis, currency, observation_date, document_type, is_credit
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(invoice_item_id) DO UPDATE SET
                   fact_id = excluded.fact_id,
                   canonical_product_id = excluded.canonical_product_id,
                   canonical_supplier_id = excluded.canonical_supplier_id,
                   observed_price = excluded.observed_price,
                   normalized_price = excluded.normalized_price,
                   normalized_unit = excluded.normalized_unit,
                   package_quantity = excluded.package_quantity,
                   package_unit = excluded.package_unit,
                   quantity = excluded.quantity,
                   vat_basis = excluded.vat_basis,
                   currency = excluded.currency,
                   observation_date = excluded.observation_date,
                   document_type = excluded.document_type,
                   is_credit = excluded.is_credit""",
            (
                fact_id, value.get("canonical_product_id"), value.get("canonical_supplier_id"),
                value["invoice_id"], value["invoice_item_id"], value.get("observed_price"),
                value.get("normalized_price"), value.get("normalized_unit", ""),
                value.get("package_quantity"), value.get("package_unit", ""),
                value.get("quantity"), value.get("vat_basis", ""), value.get("currency", ""),
                fact.observed_at, value.get("document_type", ""), int(bool(value.get("is_credit"))),
            ),
        )

    def _enqueue_conflicts(self, facts: Sequence[BusinessFact]) -> None:
        if not facts:
            return
        from services.identity_review import IdentityReviewService

        reviews = IdentityReviewService(self._connect, self.identities)
        for fact in facts:
            payload = fact.payload
            product_id = payload.get("canonical_product_id")
            supplier_id = payload.get("canonical_supplier_id")
            if fact.trust_status in {FactStatus.UNIT_CONFLICT, FactStatus.PACKAGE_CONFLICT} and product_id:
                entity_type, canonical_id = "product", int(product_id)
            elif fact.trust_status in {FactStatus.VAT_CONFLICT, FactStatus.CURRENCY_CONFLICT} and supplier_id:
                entity_type, canonical_id = "supplier", int(supplier_id)
            else:
                continue
            label = fact.trust_status.replace(" CONFLICT", "").title()
            reviews.enqueue_fact_conflict(
                review_type=fact.trust_status.casefold().replace(" ", "_"),
                entity_type=entity_type,
                canonical_id=canonical_id,
                title=f"I need help with this {label.lower()} basis",
                explanation=fact.status_explanation,
                reasons=(fact.status_explanation, "I will not compare this price until the basis is clear."),
                invoice_ids=tuple(int(value) for value in fact.evidence.get("invoice_ids", ())),
                priority=92 if fact.trust_status in {FactStatus.VAT_CONFLICT, FactStatus.UNIT_CONFLICT} else 86,
            )


class ComparablePriceLedger:
    def __init__(self, connection_factory: Callable[[], sqlite3.Connection] = connect) -> None:
        self._connect = connection_factory
        self.engine = BusinessFactsEngine(connection_factory)

    def sync(self) -> dict[str, int]:
        return self.engine.sync()

    def facts_for_invoice(self, invoice_id: int, *, ensure: bool = True) -> list[ComparablePriceFact]:
        if ensure:
            self.sync()
        return self._query("prices.invoice_id = ?", (invoice_id,))

    def fact_for_item(self, item_id: int, *, ensure: bool = True) -> ComparablePriceFact | None:
        if ensure:
            self.sync()
        values = self._query("prices.invoice_item_id = ?", (item_id,))
        return values[0] if values else None

    def history(self, canonical_product_id: int, *, trusted_only: bool = False, ensure: bool = True) -> list[ComparablePriceFact]:
        if ensure:
            self.sync()
        clause = "prices.canonical_product_id = ?"
        params: list[Any] = [canonical_product_id]
        if trusted_only:
            clause += " AND facts.trust_status = ?"
            params.append(FactStatus.TRUSTED)
        return self._query(clause, params)

    def trusted_observations(self, *, recorded_since: str = "", ensure: bool = True) -> list[ComparablePriceFact]:
        """Expose trusted ledger observations without leaking persistence queries to consumers."""
        if ensure:
            self.sync()
        clause = "facts.trust_status = ?"
        params: list[Any] = [FactStatus.TRUSTED]
        if recorded_since:
            clause += """ AND prices.invoice_id IN (
                SELECT id FROM invoices
                WHERE datetime(COALESCE(NULLIF(approved_at, ''), created_at)) >= datetime(?)
            )"""
            params.append(recorded_since)
        return self._query(clause, params)

    def previous_comparable(self, current: ComparablePriceFact, *, same_supplier: bool = True) -> PriceComparison | None:
        if not current.trusted:
            return None
        history = self.history(int(current.canonical_product_id), trusted_only=True, ensure=False)
        previous = [value for value in history if self._before(value, current)]
        if same_supplier:
            previous = [value for value in previous if value.canonical_supplier_id == current.canonical_supplier_id]
        for candidate in reversed(previous):
            comparison = self.compare(current, candidate)
            if comparison.comparable:
                return comparison
        return None

    def compare(self, current: ComparablePriceFact, previous: ComparablePriceFact) -> PriceComparison:
        status, explanation = self._comparison_status(current, previous)
        evidence = tuple(dict.fromkeys((previous.invoice_id, current.invoice_id)))
        if status != FactStatus.TRUSTED:
            return PriceComparison(current, previous, False, status, explanation, evidence_invoice_ids=evidence)
        difference = float(current.normalized_price) - float(previous.normalized_price)
        change_pct = difference / float(previous.normalized_price) * 100
        return PriceComparison(
            current, previous, True, FactStatus.TRUSTED,
            "Both prices share the same canonical product, normalized unit, VAT basis, and currency.",
            difference, change_pct, evidence,
        )

    @staticmethod
    def _comparison_status(current: ComparablePriceFact, previous: ComparablePriceFact) -> tuple[str, str]:
        if not current.trusted:
            return current.fact.trust_status, current.fact.status_explanation
        if not previous.trusted:
            return previous.fact.trust_status, previous.fact.status_explanation
        if current.canonical_product_id != previous.canonical_product_id:
            return FactStatus.IDENTITY_CONFLICT, "The prices belong to different canonical products."
        if current.invoice_id == previous.invoice_id:
            return FactStatus.NOT_COMPARABLE, "Both observations come from the same invoice, so they are not historical purchases."
        if current.normalized_unit != previous.normalized_unit:
            return FactStatus.UNIT_CONFLICT, "The prices use incompatible normalized units."
        if current.currency != previous.currency:
            return FactStatus.CURRENCY_CONFLICT, "The prices use different currencies and no exchange-rate evidence exists."
        if current.vat_basis != previous.vat_basis:
            return FactStatus.VAT_CONFLICT, "The prices use different VAT bases."
        if not current.normalized_price or not previous.normalized_price or previous.normalized_price <= 0:
            return FactStatus.NOT_COMPARABLE, "A positive normalized price is missing."
        return FactStatus.TRUSTED, "Comparable"

    @staticmethod
    def _before(left: ComparablePriceFact, right: ComparablePriceFact) -> bool:
        return (
            left.invoice_id != right.invoice_id
            and (left.observation_date, left.invoice_id) < (right.observation_date, right.invoice_id)
        )

    def _query(self, where: str, params: Sequence[Any]) -> list[ComparablePriceFact]:
        with self._connect() as connection:
            rows = connection.execute(
                f"""SELECT facts.*, prices.*,
                           products.canonical_name canonical_product_name,
                           suppliers.canonical_name canonical_supplier_name
                    FROM comparable_price_facts prices
                    JOIN business_facts facts ON facts.id = prices.fact_id
                    LEFT JOIN canonical_products products ON products.id = prices.canonical_product_id
                    LEFT JOIN canonical_suppliers suppliers ON suppliers.id = prices.canonical_supplier_id
                    WHERE {where}
                    ORDER BY prices.observation_date, prices.invoice_id, prices.invoice_item_id""",
                params,
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ComparablePriceFact:
        fact = BusinessFact(
            id=int(row["fact_id"]), fact_type=row["fact_type"], fingerprint=row["fingerprint"],
            source_type=row["source_type"], source_record_id=int(row["source_record_id"]),
            trust_status=row["trust_status"], business_confidence=float(row["business_confidence"]),
            status_explanation=row["status_explanation"],
            confidence=json.loads(row["confidence_json"] or "{}"),
            evidence=json.loads(row["evidence_json"] or "{}"),
            payload=json.loads(row["payload_json"] or "{}"), observed_at=row["observed_at"],
        )
        return ComparablePriceFact(
            fact=fact,
            canonical_product_id=row["canonical_product_id"], canonical_product_name=row["canonical_product_name"] or "",
            canonical_supplier_id=row["canonical_supplier_id"], canonical_supplier_name=row["canonical_supplier_name"] or "",
            invoice_id=int(row["invoice_id"]), invoice_item_id=int(row["invoice_item_id"]),
            observed_price=row["observed_price"], normalized_price=row["normalized_price"],
            normalized_unit=row["normalized_unit"], package_quantity=row["package_quantity"],
            package_unit=row["package_unit"], quantity=row["quantity"], vat_basis=row["vat_basis"],
            currency=row["currency"], observation_date=row["observation_date"],
            document_type=row["document_type"], is_credit=bool(row["is_credit"]),
        )


def sync_business_facts() -> dict[str, int]:
    return BusinessFactsEngine().sync()
