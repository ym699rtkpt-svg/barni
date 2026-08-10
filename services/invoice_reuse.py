"""Reuse previously approved extraction only when the source bytes are identical."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable

from database import connect


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _row_value(row: Any, key: str, default: Any = None) -> Any:
    return row[key] if key in row.keys() else default


def approved_document_for_identical_source(
    uploaded_path: Path,
    original_name: str,
    *,
    connection_factory: Callable = connect,
) -> dict[str, Any] | None:
    """Return stored structured evidence only for a byte-identical approved source."""
    with connection_factory() as connection:
        candidates = connection.execute(
            """SELECT * FROM invoices
               WHERE file_name = ? AND status = 'approved'
               ORDER BY id DESC""",
            (original_name,),
        ).fetchall()
        uploaded_digest = _digest(uploaded_path)
        matched = None
        for candidate in candidates:
            source = Path(str(candidate["archived_path"] or ""))
            if source.exists() and source.is_file() and _digest(source) == uploaded_digest:
                matched = candidate
                break
        if matched is None:
            return None
        items = connection.execute(
            """SELECT item_code, description, quantity, unit, unit_price,
                      line_total, line_type
               FROM invoice_items WHERE invoice_id = ?
               ORDER BY id""",
            (matched["id"],),
        ).fetchall()

    return {
        "document_type": matched["document_type"] or "אחר",
        "supplier": matched["supplier"] or "",
        "supplier_id": matched["supplier_id"] or "",
        "invoice_number": matched["invoice_number"] or "",
        "invoice_date": matched["invoice_date"] or "",
        "due_date": matched["due_date"] or "",
        "subtotal": matched["subtotal"],
        "taxable_amount": matched["taxable_amount"],
        "exempt_amount": matched["exempt_amount"],
        "vat_rate": matched["vat_rate"],
        "vat": matched["vat"],
        "total": matched["total"],
        "tax_treatment": matched["tax_treatment"] or "לא ברור",
        "currency": matched["currency"] or "ILS",
        "related_document_number": _row_value(matched, "related_document_number", "") or "",
        "statement_month": _row_value(matched, "statement_month", "") or "",
        "items": [dict(item) for item in items],
        "warnings": [],
        "confidence": 1.0,
        "source_invoice_id": int(matched["id"]),
    }
