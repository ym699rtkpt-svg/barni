from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
import hybrid_engine
from database import init_database
from hybrid_engine import extract_hybrid, ground_supplier_identity
from services.business_identity import BusinessIdentityRepository
from services.business_memory import business_memory_data
from services.customer_safe_errors import customer_review_reasons
from services.invoice_workflow import InvoiceWorkflowService


def _invoice_document(**overrides) -> dict:
    document = {
        "document_type": "חשבונית מס",
        "supplier": "ניצת הדובדבן",
        "supplier_id": "",
        "invoice_number": "50544",
        "invoice_date": "2026-06-24",
        "subtotal": 480.0,
        "taxable_amount": 480.0,
        "exempt_amount": 0.0,
        "vat_rate": 18.0,
        "vat": 86.4,
        "total": 566.4,
        "tax_treatment": "חייב במע״מ",
        "currency": "ILS",
        "items": [{
            "description": "כלי מטבח",
            "quantity": 1,
            "unit": "unit",
            "unit_price": 480.0,
            "line_total": 480.0,
        }],
        "confidence": 0.98,
        "warnings": [],
    }
    document.update(overrides)
    return document


class SupplierGroundingTests(unittest.TestCase):
    def test_pilot_hallucination_is_removed_and_requires_review(self):
        source_text = "חשבונית מס 50544\nתאריך 24/06/2026\nסהכ 566.40"
        with patch.object(
            hybrid_engine,
            "extract_with_ai",
            return_value=(_invoice_document(), "ai_pdf_vision"),
        ):
            document, method = extract_hybrid(
                Path("redacted-pilot.pdf"),
                raw_text=source_text,
                use_ai=True,
            )

        self.assertEqual(method, "ai_pdf_vision")
        self.assertEqual(document["supplier"], "")
        self.assertEqual(document["supplier_grounding"], "unsupported")
        self.assertIn("missing_supplier", document["machine_issues"])
        self.assertEqual(document["status"], "review")
        self.assertNotIn("ניצת הדובדבן", str(document))

    def test_source_supported_supplier_is_accepted(self):
        document = ground_supplier_identity(
            _invoice_document(supplier="ראש חץ בע\"מ", supplier_id="515123456"),
            "ראש חץ בע״מ\nח.פ. 515123456\nחשבונית מס 50544",
        )

        self.assertEqual(document["supplier"], "ראש חץ בע\"מ")
        self.assertEqual(document["supplier_id"], "515123456")
        self.assertEqual(document["supplier_grounding"], "visible_source_text")

    def test_scanned_supplier_with_exact_issuer_evidence_survives_for_review(self):
        with patch.object(
            hybrid_engine,
            "extract_with_ai",
            return_value=(
                _invoice_document(
                    supplier="רביע מדאם",
                    supplier_id="",
                    supplier_evidence={
                        "exact_text": "רביע מדאם",
                        "context": "רביע מדאם",
                        "role": "issuer",
                        "page": 1,
                        "left": 0.1,
                        "top": 0.05,
                        "right": 0.5,
                        "bottom": 0.15,
                    },
                    invoice_number="0349",
                    subtotal=1080.0,
                    taxable_amount=1080.0,
                    vat=194.4,
                    total=1274.4,
                    vat_rate=18.0,
                ),
                "ai_image_vision",
            ),
        ), patch.object(
            hybrid_engine,
            "extract_visual_supplier_evidence_text",
            return_value="רביע מדאם",
        ):
            document, _ = extract_hybrid(
                Path("redacted-rabia-madam.jpg"),
                raw_text="חשבונית 0349\nסהכ 1274.40",
                source_text_method="local_image_ocr",
            )

        self.assertEqual(document["supplier"], "רביע מדאם")
        self.assertEqual(document["supplier_grounding"], "vision_issuer_evidence")
        self.assertIn("supplier_requires_confirmation", document["model_notes"])
        self.assertNotIn("missing_supplier", document["machine_issues"])
        self.assertEqual(document["status"], "review")
        self.assertEqual(document["invoice_number"], "0349")
        self.assertEqual(document["total"], 1274.4)

    def test_unverified_vision_quote_fails_closed(self):
        document = ground_supplier_identity(
            _invoice_document(
                supplier="Plausible but unsupported supplier",
                supplier_evidence={
                    "exact_text": "Plausible but unsupported supplier",
                    "context": "Plausible but unsupported supplier",
                    "role": "issuer",
                    "page": 1,
                    "left": 0.1,
                    "top": 0.1,
                    "right": 0.7,
                    "bottom": 0.2,
                },
            ),
            "",
            extraction_method="ai_image_vision",
            visual_evidence_text="unrelated pixels",
        )

        self.assertEqual(document["supplier"], "")
        self.assertEqual(document["supplier_grounding"], "unsupported")

    def test_recipient_scoped_vision_evidence_is_rejected(self):
        document = ground_supplier_identity(
            _invoice_document(
                supplier="ניצת הדובדבן",
                supplier_evidence={
                    "exact_text": "ניצת הדובדבן",
                    "context": "לכבוד ניצת הדובדבן",
                    "role": "recipient",
                    "page": 1,
                },
            ),
            "",
            extraction_method="ai_image_vision",
        )

        self.assertEqual(document["supplier"], "")
        self.assertEqual(document["supplier_grounding"], "unsupported")
        self.assertNotIn("supplier_evidence", document)

    def test_customer_name_is_not_accepted_as_supplier_evidence(self):
        document = ground_supplier_identity(
            _invoice_document(supplier="ניצת הדובדבן"),
            "ספק אמיתי בע״מ\nח.פ. 515999111\nלכבוד\nניצת הדובדבן",
        )

        self.assertEqual(document["supplier"], "")
        self.assertEqual(document["supplier_grounding"], "unsupported")

    def test_ocr_only_supplier_is_retained_but_requires_confirmation(self):
        with patch.object(
            hybrid_engine,
            "extract_with_ai",
            return_value=(
                _invoice_document(
                    supplier="ראש חץ בע\"מ",
                    supplier_id="515123456",
                ),
                "ai_image_vision",
            ),
        ):
            document, _ = extract_hybrid(
                Path("invoice.jpg"),
                raw_text="ראש חץ בע״מ\nח.פ. 515123456\nחשבונית מס 50544",
                source_text_method="local_image_ocr",
            )

        self.assertEqual(document["supplier"], "ראש חץ בע\"מ")
        self.assertEqual(document["supplier_grounding"], "ocr_source_text")
        self.assertIn("supplier_requires_confirmation", document["model_notes"])
        self.assertEqual(document["status"], "review")
        self.assertIn(
            "I'm not completely sure about this supplier.",
            customer_review_reasons(document),
        )

    def test_unknown_supplier_cannot_enter_business_memory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "archive"
            archive.mkdir()
            source = root / "unknown.pdf"
            source.write_bytes(b"redacted evidence")
            with (
                patch.object(database, "root_dir", return_value=root),
                patch.object(database, "archive_root", return_value=archive),
            ):
                init_database(root / "invoice_archive.db")
                document = _invoice_document(supplier="")
                result = InvoiceWorkflowService().approve(
                    {"id": "unknown", "stored_file": str(source)},
                    document,
                )
                memory = business_memory_data()
                source_preserved = source.exists()

        self.assertFalse(result.success)
        self.assertEqual(memory["invoice_count"], 0)
        self.assertEqual(memory["supplier_count"], 0)
        self.assertTrue(source_preserved)

    def test_manual_correction_teaches_supplier_and_visible_id_reuses_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "archive"
            archive.mkdir()
            source = root / "corrected.pdf"
            source.write_bytes(b"redacted evidence")
            with (
                patch.object(database, "root_dir", return_value=root),
                patch.object(database, "archive_root", return_value=archive),
            ):
                init_database(root / "invoice_archive.db")
                corrected = _invoice_document(
                    supplier="ראש חץ בע\"מ",
                    supplier_id="515123456",
                )
                result = InvoiceWorkflowService().approve(
                    {"id": "manual-correction", "stored_file": str(source)},
                    corrected,
                )
                learned = BusinessIdentityRepository().supplier_identity(
                    "", "515123456", ensure=False
                )
                reused = ground_supplier_identity(
                    _invoice_document(
                        supplier="Unsupported world-knowledge name",
                        supplier_id="515123456",
                    ),
                    "חשבונית חדשה\nח.פ. 515123456\nסהכ 118.00",
                )

        self.assertTrue(result.success)
        self.assertIsNotNone(learned)
        self.assertEqual(learned.canonical_name, "ראש חץ בע\"מ")
        self.assertEqual(reused["supplier"], "ראש חץ בע\"מ")
        self.assertEqual(reused["supplier_grounding"], "approved_supplier_id")
        self.assertNotIn("Unsupported world-knowledge name", str(reused))


if __name__ == "__main__":
    unittest.main()
