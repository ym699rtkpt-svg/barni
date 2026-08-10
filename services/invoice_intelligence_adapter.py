from __future__ import annotations

from typing import Any, Mapping, Sequence

from database import search_invoices
from knowledge_engine.line_classifier import is_product_line
from services.business_facts import ComparablePriceLedger
from services.business_identity import BusinessIdentityRepository, normalize_unit
from services.invoice_intelligence import (
    Insight,
    InvoiceIntelligenceContext,
    analyze_invoice,
    select_proactive_insights,
)


def analyze_invoice_record(
    invoice: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]] | None = None,
    invoices: Sequence[Mapping[str, Any]] | None = None,
    *,
    max_insights: int = 3,
) -> list[Insight]:
    """Load existing business history and analyze one stored or draft invoice."""
    item_records = [dict(item) for item in (items if items is not None else invoice.get("items") or [])]
    use_identity_repository = invoices is None or any(
        str(item.get("description") or "").strip() for item in item_records
    )
    identities = BusinessIdentityRepository()
    if use_identity_repository:
        identities.sync_existing_memory()
    ledger = ComparablePriceLedger()
    if use_identity_repository:
        ledger.sync()
    invoice_history = (
        [dict(record) for record in invoices]
        if invoices is not None
        else search_invoices(statuses=[]).to_dict("records")
    )
    invoice_record = dict(invoice)
    if use_identity_repository and not invoice_record.get("canonical_supplier_id"):
        supplier_identity = identities.supplier_identity(
            str(invoice_record.get("supplier") or ""),
            str(invoice_record.get("supplier_id") or ""),
            ensure=False,
        )
        if supplier_identity is not None:
            invoice_record["canonical_supplier_id"] = supplier_identity.id
            invoice_record["canonical_supplier_name"] = supplier_identity.canonical_name

    for record in invoice_history:
        if record.get("canonical_supplier_id") or not use_identity_repository:
            continue
        supplier_identity = identities.supplier_identity(
            str(record.get("supplier") or ""),
            str(record.get("supplier_id") or ""),
            ensure=False,
        )
        if supplier_identity is not None:
            record["canonical_supplier_id"] = supplier_identity.id
            record["canonical_supplier_name"] = supplier_identity.canonical_name

    price_histories: dict[str, list[dict[str, Any]]] = {}
    for item in item_records:
        description = str(item.get("description") or "").strip()
        if not description or not is_product_line(item):
            continue
        product_identity = identities.product_identity(description, ensure=False)
        if product_identity is not None:
            item["canonical_product_id"] = product_identity.id
            item["canonical_product_name"] = product_identity.canonical_name
            history_records = [
                fact.as_record()
                for fact in ledger.history(product_identity.id, ensure=False)
            ]
        else:
            history_records = []
        item["normalized_unit"] = (
            str(item.get("normalized_unit") or "")
            or normalize_unit(item.get("unit"))
        )
        item_id = item.get("id") or item.get("item_id")
        if item_id:
            price_fact = ledger.fact_for_item(int(item_id), ensure=False)
            if price_fact is not None:
                item.update(price_fact.as_record())
        price_histories[description] = history_records
        canonical_name = str(item.get("canonical_product_name") or "").strip()
        if canonical_name:
            price_histories[canonical_name] = history_records

    issues = set(invoice_record.get("machine_issues") or [])
    validations: dict[str, Any] = {}
    if {"vat_rate_mismatch", "missing_vat_rate", "subtotal_mismatch"} & issues:
        validations["vat_warning"] = "The VAT rate needs your attention before approval."

    return analyze_invoice(InvoiceIntelligenceContext(
        invoice=invoice_record,
        invoices=invoice_history,
        items=item_records,
        price_histories=price_histories,
        validations=validations,
    ), max_insights=max_insights)


def analyze_proactive_invoice_record(
    invoice: Mapping[str, Any],
    items: Sequence[Mapping[str, Any]] | None = None,
    invoices: Sequence[Mapping[str, Any]] | None = None,
    *,
    max_insights: int = 3,
) -> list[Insight]:
    insights = analyze_invoice_record(
        invoice,
        items,
        invoices,
        max_insights=20,
    )
    return select_proactive_insights(insights, max_insights=max_insights)
