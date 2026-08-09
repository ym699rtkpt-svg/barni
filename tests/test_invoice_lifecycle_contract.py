from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from database import connect, init_database, search_invoices
from knowledge_engine.repository import KnowledgeRepository
from services.accountant_workspace import accountant_month_status
from services.business_memory import business_memory_data
from services.invoice_workflow import (
    ApprovalState,
    DuplicateState,
    InvoiceWorkflowService,
    InvoiceWorkflowStatus,
    build_workflow_snapshot,
    load_queue_records,
    queue_record_lifecycle,
    database_record_lifecycle,
)


class TrustedInvoiceLifecycleContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.archive = self.root / "archive"
        self.archive.mkdir(parents=True)
        self.root_patch = patch.object(database, "root_dir", return_value=self.root)
        self.archive_patch = patch.object(database, "archive_root", return_value=self.archive)
        self.root_patch.start()
        self.archive_patch.start()
        init_database(self.root / "invoice_archive.db")
        self.queue_path = self.root / "queue.json"

    def tearDown(self) -> None:
        self.archive_patch.stop()
        self.root_patch.stop()
        self.temporary.cleanup()

    def _document(self, *, number: str = "841") -> dict:
        return {
            "document_type": "invoice",
            "supplier": "Tnuva",
            "supplier_id": "vat-1",
            "invoice_number": number,
            "invoice_date": "2026-08-09",
            "subtotal": 100.0,
            "taxable_amount": 100.0,
            "vat_rate": 18.0,
            "vat": 18.0,
            "total": 118.0,
            "tax_treatment": "taxable",
            "currency": "ILS",
            "confidence": 0.99,
            "machine_issues": [],
            "model_notes": [],
            "items": [{
                "item_code": "MILK-3",
                "description": "Milk 3%",
                "quantity": 10,
                "unit": "unit",
                "unit_price": 10.0,
                "line_total": 100.0,
            }],
        }

    def _record(self, record_id: str, document: dict) -> dict:
        source = self.root / f"{record_id}.pdf"
        source.write_bytes(b"invoice evidence")
        return {
            "id": record_id,
            "stored_file": str(source),
            "queue_status": "ready",
            "document": document,
        }

    def _write_queue(self, records: list[dict]) -> None:
        self.queue_path.write_text(json.dumps(records), encoding="utf-8")

    def test_new_review_approve_learn_search_memory_and_accountant_contract(self):
        document = self._document()
        record = self._record("queue-1", document)
        self._write_queue([record])

        before = build_workflow_snapshot(
            search_invoices(statuses=[]),
            load_queue_records(self.queue_path),
        )
        self.assertEqual(before.pending_review, 1)

        result = InvoiceWorkflowService().approve(record, document)
        self.assertTrue(result.success)
        self.assertEqual(result.outcome, "saved")
        self.assertIsNotNone(result.invoice_id)

        record["queue_status"] = "approved"
        self._write_queue([record])
        after = build_workflow_snapshot(
            search_invoices(statuses=[]),
            load_queue_records(self.queue_path),
        )
        self.assertEqual(after.pending_review, 0)
        self.assertEqual(after.approved, 1)

        search_result = search_invoices(free_text="Milk 3%", statuses=["approved"])
        self.assertEqual(search_result["id"].tolist(), [result.invoice_id])

        memory = business_memory_data()
        self.assertEqual(memory["invoice_count"], 1)
        self.assertEqual(memory["supplier_count"], 1)
        self.assertEqual(memory["product_count"], 1)

        supplier_memory = KnowledgeRepository().get_supplier_memory("vat-1")
        self.assertIsNotNone(supplier_memory)
        self.assertEqual(supplier_memory["invoice_count"], 1)

        with connect() as connection:
            facts = connection.execute(
                "SELECT COUNT(*) FROM business_facts WHERE source_record_id IN "
                "(SELECT id FROM invoice_items WHERE invoice_id = ?)",
                (result.invoice_id,),
            ).fetchone()[0]
        self.assertEqual(facts, 1)

        accountant = accountant_month_status("2026-08", queue_path=self.queue_path)
        self.assertEqual(accountant["workflow"].approved, 1)
        self.assertEqual(accountant["needs_review"], 0)
        self.assertEqual(accountant["ready"], 1)
        self.assertTrue(accountant["ready_for_accountant"])

    def test_approval_retry_and_rerun_do_not_relearn_or_double_count(self):
        document = self._document()
        record = self._record("queue-retry", document)
        service = InvoiceWorkflowService()

        first = service.approve(record, document)
        second = service.approve(record, document)

        self.assertTrue(first.success)
        self.assertTrue(second.success)
        self.assertTrue(second.replayed)
        self.assertEqual(second.invoice_id, first.invoice_id)
        self.assertEqual(len(search_invoices(statuses=["approved"])), 1)

        supplier_memory = KnowledgeRepository().get_supplier_memory("vat-1")
        self.assertEqual(supplier_memory["invoice_count"], 1)
        with connect() as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM invoice_approval_operations").fetchone()[0],
                1,
            )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM business_facts").fetchone()[0],
                1,
            )

        record["queue_status"] = "approved"
        lifecycle = queue_record_lifecycle(record)
        self.assertIsNone(lifecycle.customer_state)

    def test_duplicate_needs_review_and_processing_failure_are_consistent(self):
        document = self._document()
        original = self._record("queue-original", document)
        approved = InvoiceWorkflowService().approve(original, document)
        self.assertTrue(approved.success)

        duplicate_record = self._record("queue-duplicate", document)
        duplicate = InvoiceWorkflowService().approve(duplicate_record, document)
        self.assertFalse(duplicate.success)
        self.assertEqual(duplicate.outcome, "duplicate")

        documents = search_invoices(statuses=[])
        snapshot = build_workflow_snapshot(documents, [duplicate_record])
        self.assertEqual(snapshot.duplicate, 1)
        self.assertEqual(snapshot.approved, 1)
        self.assertEqual(snapshot.open_count, 1)

        needs_review = queue_record_lifecycle({"queue_status": "review", "document": {}})
        failure = queue_record_lifecycle({"queue_status": "error", "document": {}})
        self.assertEqual(needs_review.customer_state, InvoiceWorkflowStatus.NEEDS_ATTENTION)
        self.assertEqual(failure.customer_state, InvoiceWorkflowStatus.NEEDS_ATTENTION)
        self.assertEqual(failure.processing_state.value, "failed")

    def test_retry_resumes_learning_after_failure_without_inserting_again(self):
        class FailingKnowledgeEngine:
            def handle_event(self, _event) -> None:
                raise RuntimeError("simulated learning interruption")

        document = self._document()
        record = self._record("queue-interrupted", document)
        interrupted = InvoiceWorkflowService(
            knowledge_engine=FailingKnowledgeEngine(),
        ).approve(record, document)

        self.assertFalse(interrupted.success)
        self.assertEqual(interrupted.outcome, "error")
        self.assertEqual(len(search_invoices(statuses=["approved"])), 1)

        resumed = InvoiceWorkflowService().approve(record, document)

        self.assertTrue(resumed.success)
        self.assertTrue(resumed.replayed)
        self.assertEqual(resumed.invoice_id, interrupted.invoice_id)
        self.assertEqual(len(search_invoices(statuses=["approved"])), 1)
        supplier_memory = KnowledgeRepository().get_supplier_memory("vat-1")
        self.assertEqual(supplier_memory["invoice_count"], 1)

    def test_approved_keep_both_is_resolved_not_an_open_duplicate(self):
        document = self._document()
        first_record = self._record("queue-first", document)
        self.assertTrue(InvoiceWorkflowService().approve(first_record, document).success)

        second_record = self._record("queue-second", document)
        second = InvoiceWorkflowService().approve(
            second_record,
            document,
            duplicate_resolution="keep_both",
        )
        self.assertTrue(second.success)
        self.assertEqual(second.outcome, "kept_both")

        documents = search_invoices(statuses=[])
        second_row = documents[documents["id"] == second.invoice_id].iloc[0].to_dict()
        lifecycle = database_record_lifecycle(second_row)
        self.assertEqual(lifecycle.approval_state, ApprovalState.APPROVED)
        self.assertEqual(lifecycle.duplicate_state, DuplicateState.RESOLVED_KEEP_BOTH)

        snapshot = build_workflow_snapshot(documents, [])
        self.assertEqual(snapshot.approved, 2)
        self.assertEqual(snapshot.duplicate, 0)


if __name__ == "__main__":
    unittest.main()
