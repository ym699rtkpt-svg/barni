from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from database import search_invoices


class InvoiceWorkflowStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    LEARNING = "learning"
    APPROVED = "approved"
    NEEDS_ATTENTION = "needs_attention"
    DUPLICATE = "duplicate"


STATUS_LABELS = {
    InvoiceWorkflowStatus.PENDING_REVIEW: "Pending Review",
    InvoiceWorkflowStatus.LEARNING: "Learning",
    InvoiceWorkflowStatus.APPROVED: "Approved",
    InvoiceWorkflowStatus.NEEDS_ATTENTION: "Needs Attention",
    InvoiceWorkflowStatus.DUPLICATE: "Duplicates",
}


@dataclass(frozen=True)
class InvoiceWorkflowSnapshot:
    pending_review: int = 0
    learning: int = 0
    approved: int = 0
    needs_attention: int = 0
    duplicate: int = 0

    def count(self, status: InvoiceWorkflowStatus) -> int:
        return int(getattr(self, status.value))

    @property
    def open_count(self) -> int:
        return self.pending_review + self.learning + self.needs_attention + self.duplicate

    def as_dict(self) -> dict[str, int]:
        return {
            status.value: self.count(status)
            for status in InvoiceWorkflowStatus
        }


def default_queue_path() -> Path:
    return Path.home() / "restaurant-invoices" / "daily-intake" / "queue.json"


def load_queue_records(path: Path | None = None) -> list[dict[str, Any]]:
    queue_path = path or default_queue_path()
    if not queue_path.exists():
        return []
    try:
        records = json.loads(queue_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return records if isinstance(records, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _identity(record: dict[str, Any]) -> tuple[str, str, str] | None:
    invoice_number = _text(record.get("invoice_number"))
    if not invoice_number:
        return None
    return (
        _text(record.get("supplier_id")),
        invoice_number,
        _text(record.get("document_type")),
    )


def approved_identities(documents: pd.DataFrame) -> set[tuple[str, str, str]]:
    if documents.empty:
        return set()
    identities = set()
    for record in documents.to_dict("records"):
        if _text(record.get("status")).lower() != "approved":
            continue
        identity = _identity(record)
        if identity is not None:
            identities.add(identity)
    return identities


def queue_record_status(
    record: dict[str, Any],
    *,
    known_approved: set[tuple[str, str, str]] | None = None,
) -> InvoiceWorkflowStatus | None:
    raw_status = _text(record.get("queue_status")).lower()
    if raw_status not in {"processing", "ready", "review", "error", "duplicate"}:
        return None

    document = record.get("document") or {}
    identity = _identity(document)
    if identity is not None and identity in (known_approved or set()):
        return InvoiceWorkflowStatus.DUPLICATE
    if raw_status == "duplicate":
        return InvoiceWorkflowStatus.DUPLICATE
    if raw_status == "processing":
        return InvoiceWorkflowStatus.LEARNING
    if raw_status == "ready":
        return InvoiceWorkflowStatus.PENDING_REVIEW
    return InvoiceWorkflowStatus.NEEDS_ATTENTION


def database_record_status(record: dict[str, Any]) -> InvoiceWorkflowStatus | None:
    raw_status = _text(record.get("status")).lower()
    mapping = {
        "approved": InvoiceWorkflowStatus.APPROVED,
        "review": InvoiceWorkflowStatus.NEEDS_ATTENTION,
        "needs_attention": InvoiceWorkflowStatus.NEEDS_ATTENTION,
        "pending_review": InvoiceWorkflowStatus.PENDING_REVIEW,
        "learning": InvoiceWorkflowStatus.LEARNING,
        "duplicate": InvoiceWorkflowStatus.DUPLICATE,
    }
    return mapping.get(raw_status)


def _in_month(value: Any, month: str | None) -> bool:
    return not month or _text(value).startswith(month)


def build_workflow_snapshot(
    documents: pd.DataFrame,
    queue_records: Iterable[dict[str, Any]],
    *,
    month: str | None = None,
) -> InvoiceWorkflowSnapshot:
    counts = {status: 0 for status in InvoiceWorkflowStatus}
    approved_keys = approved_identities(documents)

    if not documents.empty:
        for record in documents.to_dict("records"):
            if not _in_month(record.get("invoice_date"), month):
                continue
            status = database_record_status(record)
            if status is not None:
                counts[status] += 1

    for record in queue_records:
        document = record.get("document") or {}
        if not _in_month(document.get("invoice_date"), month):
            continue
        status = queue_record_status(record, known_approved=approved_keys)
        if status is not None:
            counts[status] += 1

    return InvoiceWorkflowSnapshot(
        pending_review=counts[InvoiceWorkflowStatus.PENDING_REVIEW],
        learning=counts[InvoiceWorkflowStatus.LEARNING],
        approved=counts[InvoiceWorkflowStatus.APPROVED],
        needs_attention=counts[InvoiceWorkflowStatus.NEEDS_ATTENTION],
        duplicate=counts[InvoiceWorkflowStatus.DUPLICATE],
    )


def build_undated_queue_snapshot(
    documents: pd.DataFrame,
    queue_records: Iterable[dict[str, Any]],
) -> InvoiceWorkflowSnapshot:
    undated = [
        record
        for record in queue_records
        if not _text((record.get("document") or {}).get("invoice_date"))
    ]
    return build_workflow_snapshot(documents, undated)


def invoice_workflow_snapshot(
    *,
    month: str | None = None,
    queue_path: Path | None = None,
) -> InvoiceWorkflowSnapshot:
    documents = search_invoices(statuses=[])
    return build_workflow_snapshot(
        documents,
        load_queue_records(queue_path),
        month=month,
    )
