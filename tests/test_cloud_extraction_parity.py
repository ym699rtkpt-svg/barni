from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import ai_extractor
import daily_intake
from ai_extractor import build_input, extraction_capability_report
from daily_intake import _load_queue, process_files


class CloudExtractionParityTests(unittest.TestCase):
    def test_full_runtime_preflight_is_ready_without_network_request(self):
        with (
            patch.object(
                ai_extractor.shutil,
                "which",
                side_effect=lambda name: f"/usr/bin/{name}",
            ),
            patch.object(
                ai_extractor,
                "_available_tesseract_languages",
                return_value={"eng", "heb"},
            ),
            patch.object(
                ai_extractor.importlib.util,
                "find_spec",
                return_value=object(),
            ),
            patch.object(ai_extractor, "OpenAI") as client,
        ):
            report = extraction_capability_report({"OPENAI_API_KEY": "configured"})

        self.assertTrue(report.ready)
        self.assertEqual(report.missing, ())
        self.assertEqual(report.internal_summary(), "Extraction runtime READY")
        client.assert_not_called()

    def test_preflight_reports_capability_names_without_secret_values(self):
        secret = "sk-private-never-log-this"
        with (
            patch.object(
                ai_extractor.shutil,
                "which",
                side_effect=lambda name: None if name == "pdftoppm" else f"/usr/bin/{name}",
            ),
            patch.object(
                ai_extractor,
                "_available_tesseract_languages",
                return_value={"eng"},
            ),
            patch.object(
                ai_extractor.importlib.util,
                "find_spec",
                side_effect=lambda name: None if name == "PIL" else object(),
            ),
        ):
            report = extraction_capability_report({"OPENAI_API_KEY": secret})

        summary = report.internal_summary()
        self.assertFalse(report.ready)
        self.assertIn("command:pdftoppm", summary)
        self.assertIn("ocr-language:heb", summary)
        self.assertIn("python-module:PIL", summary)
        self.assertNotIn(secret, summary)

    def test_embedded_text_pdf_builds_nonempty_ai_text_input(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "invoice.pdf"
            source.write_bytes(b"%PDF fixture")
            with patch.object(
                ai_extractor,
                "extract_native_pdf_text",
                return_value="חשבונית ספק " * 20,
            ):
                content, method = build_input(source)

        self.assertEqual(method, "ai_pdf_text")
        self.assertEqual([part["type"] for part in content], ["input_text"])
        self.assertTrue(content[0]["text"].strip())

    def test_scanned_pdf_falls_back_to_nonempty_page_image_input(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "scan.pdf"
            page = Path(folder) / "page-1.png"
            source.write_bytes(b"%PDF scanned fixture")
            Image.new("RGB", (8, 8), "white").save(page)
            with (
                patch.object(
                    ai_extractor,
                    "extract_native_pdf_text",
                    side_effect=FileNotFoundError("pdftotext"),
                ),
                patch.object(ai_extractor, "pdf_to_images", return_value=[page]),
            ):
                content, method = build_input(source)

        self.assertEqual(method, "ai_pdf_vision")
        self.assertEqual(
            [part["type"] for part in content],
            ["input_text", "input_image"],
        )
        self.assertTrue(content[1]["image_url"].startswith("data:image/png;base64,"))
        self.assertGreater(len(content[1]["image_url"]), 40)

    def test_image_upload_preserves_original_bytes_in_ai_input(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "invoice.jpg"
            Image.new("RGB", (8, 8), "white").save(source, format="JPEG")
            original = source.read_bytes()
            content, method = build_input(source)

        self.assertEqual(method, "ai_image_vision")
        self.assertEqual(content[1]["type"], "input_image")
        self.assertTrue(content[1]["image_url"].startswith("data:image/jpeg;base64,"))
        self.assertGreater(len(content[1]["image_url"]), len(original))

    def test_streamlit_cloud_system_packages_are_declared_once(self):
        project = Path(__file__).resolve().parents[1]
        packages = (project / "packages.txt").read_text(encoding="utf-8").splitlines()
        requirements = (project / "requirements.txt").read_text(encoding="utf-8")

        self.assertEqual(
            packages,
            [
                "poppler-utils",
                "tesseract-ocr",
                "tesseract-ocr-eng",
                "tesseract-ocr-heb",
            ],
        )
        for dependency in ("Pillow", "openai", "pydantic"):
            self.assertIn(dependency, requirements)

    def test_structured_extraction_reaches_review_without_learning(self):
        source_bytes = b"%PDF representative invoice"
        extracted = {
            "document_type": "חשבונית מס",
            "supplier": "Representative Supplier",
            "supplier_id": "515000999",
            "invoice_number": "CLOUD-1",
            "invoice_date": "2026-08-10",
            "subtotal": 100.0,
            "taxable_amount": 100.0,
            "exempt_amount": 0.0,
            "vat_rate": 18.0,
            "vat": 18.0,
            "total": 118.0,
            "tax_treatment": "חייב במע״מ",
            "currency": "ILS",
            "items": [{
                "description": "Olive Oil",
                "quantity": 1,
                "unit": "unit",
                "unit_price": 100.0,
                "line_total": 100.0,
            }],
            "confidence": 0.98,
            "warnings": [],
        }

        class Upload:
            name = "representative.pdf"

            @staticmethod
            def getbuffer() -> bytes:
                return source_bytes

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with (
                patch.object(daily_intake, "root_dir", return_value=root),
                patch.object(
                    daily_intake,
                    "approved_document_for_identical_source",
                    return_value=None,
                ),
                patch.object(
                    daily_intake,
                    "extract_document_text",
                    return_value=("usable source text", "local_pdf_text"),
                ),
                patch.object(
                    daily_intake,
                    "extract_hybrid",
                    return_value=(extracted, "ai_pdf_text"),
                ),
            ):
                process_files([Upload()], "configured-model")
                record = _load_queue(root / "daily-intake" / "queue.json")[0]
                preserved = Path(record["stored_file"]).read_bytes()

        self.assertEqual(preserved, source_bytes)
        self.assertEqual(record["queue_status"], "ready")
        self.assertEqual(record["method"], "ai_pdf_text")
        for field in ("supplier", "document_type", "invoice_number", "invoice_date", "total"):
            self.assertEqual(record["document"][field], extracted[field])


if __name__ == "__main__":
    unittest.main()
