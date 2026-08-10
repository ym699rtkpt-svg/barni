from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import database
import daily_intake
import hybrid_engine
from daily_intake import (
    _load_queue,
    _review_reason,
    _saveable_review_document,
    process_files,
)
from database import init_database
from services.invoice_workflow import InvoiceWorkflowService
from services.product_state import FirstFeedState
from ui.original_source import render_original_source


class _Upload:
    def __init__(self, name: str, data: bytes) -> None:
        self.name = name
        self._data = data

    def getbuffer(self) -> bytes:
        return self._data


class InvoiceRecoveryTests(unittest.TestCase):
    def test_problematic_pdf_is_rendered_inline_from_exact_original_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "problematic.pdf"
            original = b"%PDF-1.4\nexact uploaded evidence\n%%EOF"
            source.write_bytes(original)
            with (
                patch("ui.original_source.st.pdf") as pdf,
                patch("ui.original_source.st.download_button") as download,
            ):
                rendered = render_original_source(source, file_name="invoice.pdf")

        self.assertTrue(rendered)
        self.assertEqual(pdf.call_args.args[0], original)
        self.assertEqual(download.call_args.kwargs["data"], original)
        self.assertEqual(download.call_args.kwargs["file_name"], "invoice.pdf")

    def test_problematic_image_is_rendered_inline_from_exact_original_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "problematic.jpg"
            original = b"\xff\xd8\xffexact uploaded image\xff\xd9"
            source.write_bytes(original)
            with (
                patch("ui.original_source.st.image") as image,
                patch("ui.original_source.st.download_button") as download,
            ):
                rendered = render_original_source(source, file_name="invoice.jpg")

        self.assertTrue(rendered)
        self.assertEqual(image.call_args.args[0], original)
        self.assertEqual(download.call_args.kwargs["data"], original)

    def test_provider_failure_is_logged_but_only_safe_marker_enters_review(self):
        secret_error = RuntimeError(
            "Error 401 invalid_api_key: sk-proj-secret-fragment"
        )
        with (
            patch.object(hybrid_engine, "extract_with_ai", side_effect=secret_error),
            patch.object(hybrid_engine, "parse_invoice", return_value={}),
            patch.object(hybrid_engine, "extract_items", return_value=[]),
            patch.object(hybrid_engine, "log_runtime_error") as log_error,
        ):
            document, method = hybrid_engine.extract_hybrid(
                Path("invoice.pdf"), raw_text="", use_ai=True
            )

        rendered_reason = _review_reason({
            "queue_status": "review",
            "stored_file": "invoice.pdf",
            "document": {
                **document,
                # Legacy records may already contain raw provider text. The UI must
                # still treat it as untrusted input.
                "model_notes": [
                    *document["model_notes"],
                    str(secret_error),
                ],
            },
        })
        self.assertEqual(method, "legacy_fallback")
        self.assertEqual(document["model_notes"], ["extraction_service_unavailable"])
        self.assertNotIn("401", rendered_reason)
        self.assertNotIn("invalid_api_key", rendered_reason)
        self.assertNotIn("secret-fragment", rendered_reason)
        log_error.assert_called_once_with("Invoice extraction service", secret_error)

    def test_raw_provider_error_and_secret_fragment_never_reach_rendered_ui(self):
        app = AppTest.from_string(
            '''
from daily_intake import _render_confidence_summary
_render_confidence_summary({
    "confidence": 0.0,
    "machine_issues": ["missing_supplier"],
    "model_notes": [
        "Error 401 invalid_api_key: sk-proj-rendered-secret-fragment"
    ],
})
'''
        ).run()

        rendered = " ".join(
            str(element.value)
            for collection in (app.markdown, app.caption, app.info, app.warning, app.error)
            for element in collection
        )
        self.assertFalse(app.exception)
        self.assertIn("Some details need your attention", rendered)
        self.assertNotIn("401", rendered)
        self.assertNotIn("invalid_api_key", rendered)
        self.assertNotIn("rendered-secret-fragment", rendered)

    def test_processing_failure_preserves_source_and_does_not_complete_onboarding(self):
        original = b"%PDF-1.4\nrestaurant invoice\n%%EOF"
        provider_error = RuntimeError("401 invalid_api_key sk-secret")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state = FirstFeedState(root / "product-state.json")
            with (
                patch.object(daily_intake, "root_dir", return_value=root),
                patch.object(
                    daily_intake,
                    "extract_document_text",
                    return_value=("", "unavailable"),
                ),
                patch.object(daily_intake, "extract_hybrid", side_effect=provider_error),
                patch.object(daily_intake, "log_runtime_error") as log_error,
            ):
                process_files([_Upload("invoice.pdf", original)], "test-model")
                record = _load_queue(root / "daily-intake" / "queue.json")[0]

            preserved = Path(record["stored_file"]).read_bytes()

        self.assertEqual(preserved, original)
        self.assertEqual(record["queue_status"], "error")
        self.assertEqual(record["technical_error"], "processing_failed")
        self.assertEqual(
            set(record["document"]["machine_issues"]),
            {
                "missing_supplier",
                "missing_invoice_date",
                "missing_total",
                "missing_document_type",
            },
        )
        customer_safe_record = {
            "error": record.get("error"),
            "technical_error": record.get("technical_error"),
            "document": record.get("document"),
        }
        self.assertNotIn("401", str(customer_safe_record))
        self.assertNotIn("sk-secret", str(customer_safe_record))
        self.assertFalse(state.is_complete())
        log_error.assert_called_once_with("Feed invoice processing", provider_error)

    def test_corrected_recovery_invoice_can_be_approved_normally(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "archive"
            archive.mkdir()
            source = root / "recovered.pdf"
            source.write_bytes(b"%PDF exact original")
            with (
                patch.object(database, "root_dir", return_value=root),
                patch.object(database, "archive_root", return_value=archive),
            ):
                init_database(root / "invoice_archive.db")
                document = _saveable_review_document({
                    "document_type": "חשבונית מס",
                    "supplier": "Recovered Supplier",
                    "supplier_id": "recovered-vat",
                    "invoice_number": "REC-1",
                    "invoice_date": "2026-08-10",
                    "subtotal": 100.0,
                    "taxable_amount": 100.0,
                    "vat": 18.0,
                    "total": 118.0,
                    "tax_treatment": "חייב במע״מ",
                    "currency": "ILS",
                    "items": [{
                        "description": "Tomatoes",
                        "quantity": 10,
                        "unit": "kg",
                        "unit_price": 10.0,
                        "line_total": 100.0,
                    }],
                    "warnings": ["extraction_service_unavailable"],
                })
                self.assertFalse(document["machine_issues"])
                result = InvoiceWorkflowService().approve(
                    {
                        "id": "recovered-review",
                        "stored_file": str(source),
                        "queue_status": "review",
                    },
                    document,
                )

                self.assertTrue(result.success)
                self.assertTrue(FirstFeedState().is_complete())
                self.assertEqual((archive / "2026" / "08" / "recovered.pdf").read_bytes(), b"%PDF exact original")


if __name__ == "__main__":
    unittest.main()
