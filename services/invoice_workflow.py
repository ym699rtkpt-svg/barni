from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import pandas as pd

from database import (
    connect,
    duplicate_invoice,
    insert_invoice,
    replace_duplicate_invoice,
    search_invoices,
)
from knowledge_engine.engine import KnowledgeEngine
from knowledge_engine.events import KnowledgeEvent
from services.business_facts import ComparablePriceLedger


class ProcessingState(str, Enum):
    NOT_STARTED = "not_started"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class ReviewState(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    NEEDS_ATTENTION = "needs_attention"
    RESOLVED = "resolved"


class ApprovalState(str, Enum):
    NOT_APPROVED = "not_approved"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class DuplicateState(str, Enum):
    NOT_CHECKED = "not_checked"
    UNIQUE = "unique"
    NEEDS_DECISION = "needs_decision"
    RESOLVED_SKIPPED = "resolved_skipped"
    RESOLVED_REPLACED = "resolved_replaced"
    RESOLVED_KEEP_BOTH = "resolved_keep_both"


class AccountingReadiness(str, Enum):
    NOT_APPLICABLE = "not_applicable"
    BLOCKED = "blocked"
    READY = "ready"


class InvoiceWorkflowStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    LEARNING = "learning"
    APPROVED = "approved"
    NEEDS_ATTENTION = "needs_attention"
    DUPLICATE = "duplicate"


@dataclass(frozen=True)
class InvoiceLifecycleState:
    processing_state: ProcessingState
    review_state: ReviewState
    approval_state: ApprovalState
    duplicate_state: DuplicateState
    accounting_readiness: AccountingReadiness
    customer_state: InvoiceWorkflowStatus | None
    reason: str = ""


@dataclass(frozen=True)
class ApprovalResult:
    success: bool
    message: str
    outcome: str
    invoice_id: int | None = None
    existing: Mapping[str, Any] | None = None
    replayed: bool = False

    def as_legacy_tuple(self) -> tuple[bool, str, dict[str, Any]]:
        payload: dict[str, Any] = {
            "outcome": self.outcome,
            "invoice_id": self.invoice_id,
        }
        if self.existing is not None:
            payload["existing"] = dict(self.existing)
        if self.replayed:
            payload["replayed"] = True
        return self.success, self.message, payload


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
    accounting_ready: int = 0
    accounting_blocked: int = 0

    def count(self, status: InvoiceWorkflowStatus) -> int:
        return int(getattr(self, status.value))

    @property
    def open_count(self) -> int:
        return self.pending_review + self.learning + self.needs_attention + self.duplicate

    def as_dict(self) -> dict[str, int]:
        values = {
            status.value: self.count(status)
            for status in InvoiceWorkflowStatus
        }
        values.update({
            "accounting_ready": self.accounting_ready,
            "accounting_blocked": self.accounting_blocked,
        })
        return values


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


def queue_record_lifecycle(
    record: dict[str, Any],
    *,
    known_approved: set[tuple[str, str, str]] | None = None,
) -> InvoiceLifecycleState:
    raw_status = _text(record.get("queue_status")).lower()
    document = record.get("document") or {}
    identity = _identity(document)
    is_duplicate = (
        raw_status == "duplicate"
        or (identity is not None and identity in (known_approved or set()))
    )

    if raw_status in {"approved", "skipped", "rejected"}:
        approval = {
            "approved": ApprovalState.APPROVED,
            "skipped": ApprovalState.SKIPPED,
            "rejected": ApprovalState.REJECTED,
        }[raw_status]
        duplicate = (
            DuplicateState.RESOLVED_SKIPPED
            if raw_status == "skipped"
            else DuplicateState.UNIQUE
        )
        return InvoiceLifecycleState(
            ProcessingState.COMPLETE,
            ReviewState.RESOLVED,
            approval,
            duplicate,
            AccountingReadiness.READY if approval == ApprovalState.APPROVED else AccountingReadiness.NOT_APPLICABLE,
            None,
            "This queue record is resolved.",
        )

    if is_duplicate:
        return InvoiceLifecycleState(
            ProcessingState.COMPLETE,
            ReviewState.NEEDS_ATTENTION,
            ApprovalState.NOT_APPROVED,
            DuplicateState.NEEDS_DECISION,
            AccountingReadiness.BLOCKED,
            InvoiceWorkflowStatus.DUPLICATE,
            "A matching approved invoice requires a duplicate decision.",
        )
    if raw_status == "processing":
        return InvoiceLifecycleState(
            ProcessingState.PROCESSING,
            ReviewState.NOT_REQUIRED,
            ApprovalState.NOT_APPROVED,
            DuplicateState.NOT_CHECKED,
            AccountingReadiness.BLOCKED,
            InvoiceWorkflowStatus.LEARNING,
            "Barni is processing this invoice.",
        )
    if raw_status == "ready":
        return InvoiceLifecycleState(
            ProcessingState.COMPLETE,
            ReviewState.PENDING,
            ApprovalState.NOT_APPROVED,
            DuplicateState.UNIQUE,
            AccountingReadiness.BLOCKED,
            InvoiceWorkflowStatus.PENDING_REVIEW,
            "This invoice is ready for approval.",
        )
    if raw_status in {"review", "error"}:
        return InvoiceLifecycleState(
            ProcessingState.FAILED if raw_status == "error" else ProcessingState.COMPLETE,
            ReviewState.NEEDS_ATTENTION,
            ApprovalState.NOT_APPROVED,
            DuplicateState.NOT_CHECKED,
            AccountingReadiness.BLOCKED,
            InvoiceWorkflowStatus.NEEDS_ATTENTION,
            "Processing failed." if raw_status == "error" else "One or more details need review.",
        )
    return InvoiceLifecycleState(
        ProcessingState.NOT_STARTED,
        ReviewState.NOT_REQUIRED,
        ApprovalState.NOT_APPROVED,
        DuplicateState.NOT_CHECKED,
        AccountingReadiness.NOT_APPLICABLE,
        None,
        "This record does not participate in the active customer workflow.",
    )


def queue_record_status(
    record: dict[str, Any],
    *,
    known_approved: set[tuple[str, str, str]] | None = None,
) -> InvoiceWorkflowStatus | None:
    """Compatibility projection; customer state is derived from the canonical model."""
    return queue_record_lifecycle(record, known_approved=known_approved).customer_state


def database_record_lifecycle(record: dict[str, Any]) -> InvoiceLifecycleState:
    raw_status = _text(record.get("status")).lower()
    source_path = _text(record.get("archived_path"))
    source_available = bool(source_path) and Path(source_path).exists()
    supplier_available = bool(_text(record.get("supplier")))
    if raw_status == "approved":
        approval_outcome = _text(record.get("approval_outcome"))
        duplicate_state = {
            "replaced": DuplicateState.RESOLVED_REPLACED,
            "kept_both": DuplicateState.RESOLVED_KEEP_BOTH,
        }.get(approval_outcome, DuplicateState.UNIQUE)
        readiness = (
            AccountingReadiness.READY
            if source_available and supplier_available
            else AccountingReadiness.BLOCKED
        )
        return InvoiceLifecycleState(
            ProcessingState.COMPLETE,
            ReviewState.RESOLVED,
            ApprovalState.APPROVED,
            duplicate_state,
            readiness,
            InvoiceWorkflowStatus.APPROVED,
            "This invoice is approved.",
        )
    if raw_status in {"review", "needs_attention"}:
        customer = InvoiceWorkflowStatus.NEEDS_ATTENTION
        review = ReviewState.NEEDS_ATTENTION
    elif raw_status == "pending_review":
        customer = InvoiceWorkflowStatus.PENDING_REVIEW
        review = ReviewState.PENDING
    elif raw_status == "learning":
        return InvoiceLifecycleState(
            ProcessingState.PROCESSING,
            ReviewState.NOT_REQUIRED,
            ApprovalState.NOT_APPROVED,
            DuplicateState.NOT_CHECKED,
            AccountingReadiness.BLOCKED,
            InvoiceWorkflowStatus.LEARNING,
            "Barni is learning from this invoice.",
        )
    elif raw_status == "duplicate":
        return InvoiceLifecycleState(
            ProcessingState.COMPLETE,
            ReviewState.NEEDS_ATTENTION,
            ApprovalState.NOT_APPROVED,
            DuplicateState.NEEDS_DECISION,
            AccountingReadiness.BLOCKED,
            InvoiceWorkflowStatus.DUPLICATE,
            "A duplicate decision is required.",
        )
    else:
        return InvoiceLifecycleState(
            ProcessingState.COMPLETE,
            ReviewState.RESOLVED,
            ApprovalState.REJECTED if raw_status == "rejected" else ApprovalState.NOT_APPROVED,
            DuplicateState.NOT_CHECKED,
            AccountingReadiness.NOT_APPLICABLE,
            None,
            "This stored record is outside the active workflow.",
        )
    return InvoiceLifecycleState(
        ProcessingState.COMPLETE,
        review,
        ApprovalState.NOT_APPROVED,
        DuplicateState.NOT_CHECKED,
        AccountingReadiness.BLOCKED,
        customer,
        "This invoice needs review.",
    )


def database_record_status(record: dict[str, Any]) -> InvoiceWorkflowStatus | None:
    """Compatibility projection; customer state is derived from the canonical model."""
    return database_record_lifecycle(record).customer_state


def database_status_label(value: Any) -> str:
    lifecycle = database_record_lifecycle({"status": value})
    if lifecycle.customer_state is not None:
        return STATUS_LABELS[lifecycle.customer_state]
    if lifecycle.approval_state == ApprovalState.REJECTED:
        return "Rejected"
    return "Not in active workflow"


def _in_month(value: Any, month: str | None) -> bool:
    return not month or _text(value).startswith(month)


def build_workflow_snapshot(
    documents: pd.DataFrame,
    queue_records: Iterable[dict[str, Any]],
    *,
    month: str | None = None,
) -> InvoiceWorkflowSnapshot:
    counts = {status: 0 for status in InvoiceWorkflowStatus}
    accounting_counts = {state: 0 for state in AccountingReadiness}
    approved_keys = approved_identities(documents)

    if not documents.empty:
        for record in documents.to_dict("records"):
            if not _in_month(record.get("invoice_date"), month):
                continue
            lifecycle = database_record_lifecycle(record)
            if lifecycle.customer_state is not None:
                counts[lifecycle.customer_state] += 1
            accounting_counts[lifecycle.accounting_readiness] += 1

    for record in queue_records:
        document = record.get("document") or {}
        if not _in_month(document.get("invoice_date"), month):
            continue
        lifecycle = queue_record_lifecycle(record, known_approved=approved_keys)
        if lifecycle.customer_state is not None:
            counts[lifecycle.customer_state] += 1
        accounting_counts[lifecycle.accounting_readiness] += 1

    return InvoiceWorkflowSnapshot(
        pending_review=counts[InvoiceWorkflowStatus.PENDING_REVIEW],
        learning=counts[InvoiceWorkflowStatus.LEARNING],
        approved=counts[InvoiceWorkflowStatus.APPROVED],
        needs_attention=counts[InvoiceWorkflowStatus.NEEDS_ATTENTION],
        duplicate=counts[InvoiceWorkflowStatus.DUPLICATE],
        accounting_ready=accounting_counts[AccountingReadiness.READY],
        accounting_blocked=accounting_counts[AccountingReadiness.BLOCKED],
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


def approved_documents() -> pd.DataFrame:
    """Return the one canonical set of invoices approved for customer memory."""
    documents = search_invoices(statuses=[])
    if documents.empty:
        return documents
    mask = documents.apply(
        lambda row: database_record_lifecycle(row.to_dict()).approval_state
        == ApprovalState.APPROVED,
        axis=1,
    )
    return documents[mask].copy()


def approval_operation_key(record: Mapping[str, Any], document: Mapping[str, Any]) -> str:
    """Build a stable retry key for one Feed/Review record."""
    explicit = _text(record.get("id") or record.get("approval_key"))
    if explicit:
        return f"invoice:{explicit}"
    stable_parts = [
        _text(record.get("stored_file")),
        _text(document.get("supplier_id")),
        _text(document.get("invoice_number")),
        _text(document.get("document_type")),
        _text(document.get("invoice_date")),
    ]
    digest = hashlib.sha256("\x1f".join(stable_parts).encode("utf-8")).hexdigest()
    return f"invoice:{digest}"


class InvoiceWorkflowService:
    """Authoritative invoice approval and lifecycle application service."""

    def __init__(
        self,
        *,
        connection_factory: Callable = connect,
        knowledge_engine: KnowledgeEngine | None = None,
        price_ledger: ComparablePriceLedger | None = None,
    ) -> None:
        self._connect = connection_factory
        self._knowledge = knowledge_engine or KnowledgeEngine()
        self._ledger = price_ledger or ComparablePriceLedger(connection_factory)

    def approve(
        self,
        record: Mapping[str, Any],
        document: Mapping[str, Any],
        *,
        duplicate_resolution: str = "ask",
        on_progress: Callable[[str], None] | None = None,
    ) -> ApprovalResult:
        notify = on_progress or (lambda _stage: None)
        operation_key = approval_operation_key(record, document)
        previous = self._operation(operation_key)
        if previous and previous["operation_status"] == "completed":
            outcome = _text(previous["outcome"])
            message = (
                "החשבונית החדשה דולגה לפי בחירתך."
                if outcome == "skipped"
                else self._success_message(previous["invoice_id"])
            )
            return ApprovalResult(
                True,
                message,
                outcome,
                previous["invoice_id"],
                replayed=True,
            )

        self._begin_operation(operation_key, duplicate_resolution)
        source = Path(_text(record.get("stored_file")))
        existing_by_key = self._invoice_for_approval_key(operation_key)
        outcome = _text(previous["outcome"]) if previous else ""
        invoice_id = int(existing_by_key["id"]) if existing_by_key else None

        try:
            if invoice_id is None:
                notify("duplicate_check")
                existing = duplicate_invoice(
                    _text(document.get("supplier_id")),
                    _text(document.get("invoice_number")),
                    _text(document.get("document_type")),
                )
                if existing and duplicate_resolution == "ask":
                    self._set_operation(
                        operation_key,
                        status="awaiting_duplicate",
                        outcome="duplicate",
                        invoice_id=int(existing["id"]),
                    )
                    return ApprovalResult(
                        False,
                        "כבר קיים מסמך עם אותו ספק, מספר וסוג.",
                        "duplicate",
                        int(existing["id"]),
                        existing,
                    )
                if existing and duplicate_resolution == "skip":
                    self._complete_operation(
                        operation_key,
                        outcome="skipped",
                        invoice_id=int(existing["id"]),
                    )
                    return ApprovalResult(
                        True,
                        "החשבונית החדשה דולגה לפי בחירתך.",
                        "skipped",
                        int(existing["id"]),
                        existing,
                    )

                notify("saving")
                if existing and duplicate_resolution == "replace":
                    outcome = "replaced"
                    self._set_operation(operation_key, status="processing", outcome=outcome)
                    invoice_id = replace_duplicate_invoice(
                        int(existing["id"]),
                        source,
                        dict(document),
                        approval_key=operation_key,
                    )
                else:
                    outcome = "kept_both" if existing else "saved"
                    self._set_operation(operation_key, status="processing", outcome=outcome)
                    invoice_id = insert_invoice(
                        source_file=source,
                        document=dict(document),
                        move_source=True,
                        approval_key=operation_key,
                    )
                self._set_operation(
                    operation_key,
                    status="processing",
                    outcome=outcome,
                    invoice_id=invoice_id,
                )

            notify("learning")
            self._learn_once(invoice_id, document)
            self._complete_operation(operation_key, outcome=outcome or "saved", invoice_id=invoice_id)
            return ApprovalResult(
                True,
                self._success_message(invoice_id),
                outcome or "saved",
                invoice_id,
                replayed=existing_by_key is not None,
            )
        except Exception as exc:
            self._set_operation(
                operation_key,
                status="failed",
                outcome=outcome,
                invoice_id=invoice_id,
                error=str(exc),
            )
            return ApprovalResult(False, str(exc), "error", invoice_id)

    def _learn_once(self, invoice_id: int, document: Mapping[str, Any]) -> None:
        event = KnowledgeEvent(
            event_type="invoice_approved",
            payload={**dict(document), "invoice_id": invoice_id},
            created_at=datetime.now(),
        )
        self._knowledge.handle_event(event)
        self._ledger.sync()

    def _operation(self, operation_key: str):
        with self._connect() as connection:
            return connection.execute(
                "SELECT * FROM invoice_approval_operations WHERE operation_key = ?",
                (operation_key,),
            ).fetchone()

    def _invoice_for_approval_key(self, operation_key: str):
        with self._connect() as connection:
            return connection.execute(
                "SELECT * FROM invoices WHERE approval_key = ?",
                (operation_key,),
            ).fetchone()

    def _begin_operation(self, operation_key: str, duplicate_resolution: str) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO invoice_approval_operations(
                       operation_key, operation_status, duplicate_resolution,
                       created_at, updated_at
                   ) VALUES (?, 'processing', ?, ?, ?)
                   ON CONFLICT(operation_key) DO UPDATE SET
                       operation_status = CASE
                           WHEN invoice_approval_operations.operation_status = 'completed'
                           THEN 'completed' ELSE 'processing' END,
                       duplicate_resolution = excluded.duplicate_resolution,
                       error = '', updated_at = excluded.updated_at""",
                (operation_key, duplicate_resolution, now, now),
            )
            connection.commit()

    def _set_operation(
        self,
        operation_key: str,
        *,
        status: str,
        outcome: str = "",
        invoice_id: int | None = None,
        error: str = "",
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """UPDATE invoice_approval_operations
                   SET operation_status = ?, outcome = ?, invoice_id = COALESCE(?, invoice_id),
                       error = ?, updated_at = ?
                   WHERE operation_key = ?""",
                (
                    status,
                    outcome,
                    invoice_id,
                    error,
                    datetime.now().isoformat(timespec="seconds"),
                    operation_key,
                ),
            )
            connection.commit()

    def _complete_operation(self, operation_key: str, *, outcome: str, invoice_id: int) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                """UPDATE invoice_approval_operations
                   SET operation_status = 'completed', outcome = ?, invoice_id = ?,
                       error = '', updated_at = ?, completed_at = ?
                   WHERE operation_key = ?""",
                (outcome, invoice_id, now, now, operation_key),
            )
            connection.commit()

    @staticmethod
    def _success_message(invoice_id: int | None) -> str:
        return f"המסמך נשמר במסד ובארכיון. מזהה: {invoice_id}"
