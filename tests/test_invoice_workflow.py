from __future__ import annotations

import unittest

import pandas as pd

from services.invoice_workflow import (
    AccountingReadiness,
    ApprovalState,
    DuplicateState,
    InvoiceWorkflowStatus,
    ProcessingState,
    ReviewState,
    build_undated_queue_snapshot,
    build_workflow_snapshot,
    database_record_lifecycle,
    queue_record_lifecycle,
    queue_record_status,
)


class InvoiceWorkflowStatusTests(unittest.TestCase):
    def setUp(self):
        self.documents = pd.DataFrame(
            [
                {
                    "id": 1,
                    "status": "approved",
                    "supplier_id": "supplier-a",
                    "invoice_number": "100",
                    "document_type": "invoice",
                    "invoice_date": "2026-08-01",
                },
                {
                    "id": 2,
                    "status": "approved",
                    "supplier_id": "supplier-b",
                    "invoice_number": "200",
                    "document_type": "invoice",
                    "invoice_date": "2026-07-20",
                },
            ]
        )

    def test_snapshot_uses_one_exclusive_status_for_each_open_queue_record(self):
        queue = [
            {
                "queue_status": "ready",
                "document": {"invoice_date": "2026-08-02"},
            },
            {
                "queue_status": "review",
                "document": {"invoice_date": "2026-08-03"},
            },
            {
                "queue_status": "processing",
                "document": {"invoice_date": "2026-08-04"},
            },
            {
                "queue_status": "ready",
                "document": {
                    "supplier_id": "supplier-a",
                    "invoice_number": "100",
                    "document_type": "invoice",
                    "invoice_date": "2026-08-05",
                },
            },
        ]

        snapshot = build_workflow_snapshot(self.documents, queue)

        self.assertEqual(snapshot.approved, 2)
        self.assertEqual(snapshot.pending_review, 1)
        self.assertEqual(snapshot.learning, 1)
        self.assertEqual(snapshot.needs_attention, 1)
        self.assertEqual(snapshot.duplicate, 1)
        self.assertEqual(snapshot.open_count, 4)

    def test_month_scope_uses_the_same_status_rules(self):
        queue = [
            {
                "queue_status": "ready",
                "document": {"invoice_date": "2026-08-02"},
            },
            {
                "queue_status": "review",
                "document": {"invoice_date": "2026-07-02"},
            },
        ]

        snapshot = build_workflow_snapshot(self.documents, queue, month="2026-08")

        self.assertEqual(snapshot.approved, 1)
        self.assertEqual(snapshot.pending_review, 1)
        self.assertEqual(snapshot.needs_attention, 0)

    def test_resolved_queue_records_are_not_counted(self):
        for raw_status in ("approved", "skipped", "rejected"):
            with self.subTest(raw_status=raw_status):
                status = queue_record_status({"queue_status": raw_status})
                self.assertIsNone(status)

    def test_database_review_status_maps_to_needs_attention(self):
        documents = pd.DataFrame(
            [{"status": "review", "invoice_date": "2026-08-01"}]
        )

        snapshot = build_workflow_snapshot(documents, [])

        self.assertEqual(snapshot.needs_attention, 1)
        self.assertEqual(
            snapshot.count(InvoiceWorkflowStatus.NEEDS_ATTENTION),
            1,
        )

    def test_approval_transition_moves_one_invoice_from_pending_to_approved(self):
        pending_record = {
            "queue_status": "ready",
            "document": {
                "supplier_id": "supplier-c",
                "invoice_number": "300",
                "document_type": "invoice",
                "invoice_date": "2026-08-06",
            },
        }
        before = build_workflow_snapshot(self.documents, [pending_record])

        approved_documents = pd.concat(
            [
                self.documents,
                pd.DataFrame(
                    [
                        {
                            "id": 3,
                            "status": "approved",
                            **pending_record["document"],
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        after = build_workflow_snapshot(approved_documents, [])

        self.assertEqual(before.pending_review, 1)
        self.assertEqual(after.pending_review, 0)
        self.assertEqual(after.approved, before.approved + 1)

    def test_undated_open_work_is_kept_visible_for_readiness(self):
        queue = [
            {"queue_status": "error", "document": {"invoice_date": ""}},
            {"queue_status": "ready", "document": {"invoice_date": "2026-08-02"}},
        ]

        snapshot = build_undated_queue_snapshot(self.documents, queue)

        self.assertEqual(snapshot.needs_attention, 1)
        self.assertEqual(snapshot.pending_review, 0)

    def test_canonical_model_keeps_lifecycle_concerns_separate(self):
        lifecycle = queue_record_lifecycle({
            "queue_status": "error",
            "document": {"invoice_date": "2026-08-02"},
        })

        self.assertEqual(lifecycle.processing_state, ProcessingState.FAILED)
        self.assertEqual(lifecycle.review_state, ReviewState.NEEDS_ATTENTION)
        self.assertEqual(lifecycle.approval_state, ApprovalState.NOT_APPROVED)
        self.assertEqual(lifecycle.duplicate_state, DuplicateState.NOT_CHECKED)
        self.assertEqual(lifecycle.accounting_readiness, AccountingReadiness.BLOCKED)
        self.assertEqual(lifecycle.customer_state, InvoiceWorkflowStatus.NEEDS_ATTENTION)

    def test_approved_database_record_has_one_customer_state(self):
        lifecycle = database_record_lifecycle({
            "status": "approved",
            "supplier": "Tnuva",
            "archived_path": "/archive/invoice.pdf",
        })

        self.assertEqual(lifecycle.approval_state, ApprovalState.APPROVED)
        self.assertEqual(lifecycle.customer_state, InvoiceWorkflowStatus.APPROVED)
        self.assertEqual(lifecycle.accounting_readiness, AccountingReadiness.BLOCKED)


if __name__ == "__main__":
    unittest.main()
