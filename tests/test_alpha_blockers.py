from __future__ import annotations

import io
import json
import sqlite3
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from daily_intake import (
    _approval_blockers, _load_queue, _records_requiring_review,
    _save_queue, _status_for, process_files,
)
from database import init_database, root_dir
from services.accountant_workspace import build_accountant_package
from services.invoice_reuse import approved_document_for_identical_source
from services.invoice_workflow import load_queue_records
from smart_archive import _memory_suggestions
from ui.accountant_workspace import _prepare_accountant_package


class AlphaBlockerTests(unittest.TestCase):
    def test_identical_approved_source_reuses_populated_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db_path = root / "test.db"
            source = root / "invoice.pdf"
            upload = root / "copy.pdf"
            source.write_bytes(b"same invoice bytes")
            upload.write_bytes(source.read_bytes())
            init_database(db_path)

            def connection_factory():
                connection = sqlite3.connect(db_path)
                connection.row_factory = sqlite3.Row
                return connection

            with connection_factory() as connection:
                connection.execute(
                    """INSERT INTO invoices(
                           id, file_name, archived_path, supplier, supplier_id,
                           invoice_number, invoice_date, document_type, total,
                           currency, status, created_at, approved_at, updated_at
                       ) VALUES (1, 'invoice.pdf', ?, 'Supplier', '123', '841',
                                 '2026-08-01', 'חשבונית מס', 100, 'ILS',
                                 'approved', '2026-08-01', '2026-08-01', '2026-08-01')""",
                    (str(source),),
                )
                connection.execute(
                    """INSERT INTO invoice_items(
                           invoice_id, description, quantity, unit_price, line_total, line_type
                       ) VALUES (1, 'Milk', 1, 10, 10, 'product')"""
                )

            document = approved_document_for_identical_source(
                upload, "invoice.pdf", connection_factory=connection_factory
            )
            self.assertEqual(document["supplier"], "Supplier")
            self.assertEqual(document["invoice_number"], "841")
            self.assertEqual(document["items"][0]["description"], "Milk")

    def test_different_source_never_reuses_stored_extraction(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db_path = root / "test.db"
            source = root / "invoice.pdf"
            upload = root / "copy.pdf"
            source.write_bytes(b"original")
            upload.write_bytes(b"different")
            init_database(db_path)

            def connection_factory():
                connection = sqlite3.connect(db_path)
                connection.row_factory = sqlite3.Row
                return connection

            with connection_factory() as connection:
                connection.execute(
                    """INSERT INTO invoices(
                           file_name, archived_path, status, created_at, approved_at, updated_at
                       ) VALUES ('invoice.pdf', ?, 'approved', '2026-08-01',
                                 '2026-08-01', '2026-08-01')""",
                    (str(source),),
                )
            self.assertIsNone(approved_document_for_identical_source(
                upload, "invoice.pdf", connection_factory=connection_factory
            ))

    def test_blank_review_cannot_be_approved(self):
        blockers = _approval_blockers({"document_type": "חשבונית מס", "items": []})
        self.assertIn("supplier", blockers)
        self.assertIn("invoice date", blockers)
        self.assertIn("total", blockers)
        self.assertIn("at least one product", blockers)

    def test_populated_receipt_can_be_approved_without_products(self):
        self.assertEqual(_approval_blockers({
            "document_type": "קבלה", "supplier": "Supplier",
            "invoice_date": "2026-08-01", "total": 100, "items": [],
        }), [])

    def test_only_uncertain_invoices_enter_review(self):
        records = [
            {"id": "clear", "queue_status": "ready", "document": {}},
            {"id": "uncertain", "queue_status": "review", "document": {}},
            {"id": "failed", "queue_status": "error", "document": {}},
        ]
        self.assertEqual(
            _records_requiring_review(records),
            ["uncertain", "failed"],
        )

    def test_review_edits_do_not_mark_incomplete_invoice_ready(self):
        self.assertEqual(_status_for({
            "document_type": "חשבונית מס",
            "supplier": "",
            "invoice_date": "",
            "total": None,
            "items": [],
            "confidence": 0.99,
        }), "review")

    def test_queue_write_is_atomic_and_corrupt_primary_recovers_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            queue_path = Path(folder) / "queue.json"
            first = [{"id": "first", "queue_status": "review"}]
            second = [{"id": "second", "queue_status": "ready"}]
            _save_queue(queue_path, first)
            _save_queue(queue_path, second)

            self.assertEqual(_load_queue(queue_path), second)
            queue_path.write_text("{broken", encoding="utf-8")
            self.assertEqual(_load_queue(queue_path), first)
            self.assertEqual(load_queue_records(queue_path), first)

    def test_isolated_data_root_does_not_use_live_business_workspace(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict("os.environ", {"BARNI_DATA_ROOT": folder}):
                self.assertEqual(root_dir(), Path(folder))

    def test_upload_persistence_failure_enters_recoverable_review(self):
        class FailedUpload:
            name = "invoice.pdf"

            @staticmethod
            def getbuffer():
                raise OSError("private storage detail")

        with tempfile.TemporaryDirectory() as folder:
            with patch.dict("os.environ", {"BARNI_DATA_ROOT": folder}):
                process_files([FailedUpload()], "test-model")
                records = _load_queue(Path(folder) / "daily-intake" / "queue.json")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["queue_status"], "error")
        self.assertIn("Try a clearer copy", records[0]["error"])
        self.assertNotIn("private storage detail", records[0]["error"])

    def test_ocr_timeout_keeps_file_in_recoverable_review(self):
        class UploadedInvoice:
            name = "invoice.pdf"

            @staticmethod
            def getbuffer():
                return b"invoice bytes"

        with tempfile.TemporaryDirectory() as folder:
            with (
                patch.dict("os.environ", {"BARNI_DATA_ROOT": folder}),
                patch("daily_intake.approved_document_for_identical_source", return_value=None),
                patch(
                    "daily_intake.extract_document_text",
                    side_effect=subprocess.TimeoutExpired("ocr", 90),
                ),
            ):
                process_files([UploadedInvoice()], "test-model")
                records = _load_queue(Path(folder) / "daily-intake" / "queue.json")
                stored_file_exists = Path(records[0]["stored_file"]).exists()

        self.assertEqual(records[0]["queue_status"], "error")
        self.assertTrue(stored_file_exists)
        self.assertNotIn("ocr", records[0]["error"].lower())

    def test_export_failure_returns_customer_recovery_without_raising(self):
        with (
            patch("ui.accountant_workspace.build_accountant_package", side_effect=OSError("secret path")),
            patch("ui.accountant_workspace.log_runtime_error"),
        ):
            package, recovery = _prepare_accountant_package({})

        self.assertIsNone(package)
        self.assertIn("Nothing was exported", recovery)
        self.assertIn("try again", recovery)
        self.assertNotIn("secret path", recovery)

    def test_search_suggestions_are_real_memory_values(self):
        self.assertEqual(
            _memory_suggestions(["Milk", "Tomatoes"], ["Tnuva", "Tnuva"]),
            ["Milk", "Tomatoes", "Tnuva"],
        )

    def test_accountant_package_contains_required_artifacts_and_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "invoice.pdf"
            source.write_bytes(b"invoice")
            documents = pd.DataFrame([{
                "id": 1, "invoice_date": "2026-08-01", "supplier": "Supplier",
                "invoice_number": "841", "total": 100, "archived_path": str(source),
            }])
            status = {
                "month": "2026-08", "documents": documents, "ready": 1,
                "missing": 0, "duplicate": 0, "needs_review": 0,
                "missing_supplier_names": 0, "total": 100,
                "ready_for_accountant": True, "uploaded": 1, "issues": [],
            }
            package = zipfile.ZipFile(io.BytesIO(build_accountant_package(status)))
            self.assertIn("summary.csv", package.namelist())
            self.assertIn("summary.pdf", package.namelist())
            self.assertIn("metadata.json", package.namelist())
            self.assertIn("invoices/1_invoice.pdf", package.namelist())
            self.assertEqual(json.loads(package.read("metadata.json"))["invoice_count"], 1)


if __name__ == "__main__":
    unittest.main()
