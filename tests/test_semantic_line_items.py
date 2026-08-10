from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import database
from database import connect, init_database, invoice_items
from knowledge_engine.line_classifier import (
    SemanticLineType,
    classify_invoice_item,
    classify_invoice_line,
)
from services.accountant_workspace import accountant_month_status, build_accountant_package
from services.business_facts import ComparablePriceLedger
from services.business_identity import BusinessIdentityRepository
from services.business_memory import business_memory_data, product_memory_options
from services.invoice_reuse import approved_document_for_identical_source
from services.invoice_workflow import InvoiceWorkflowService
from services.visible_learning import capture_learning_snapshot


class SemanticLineItemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.archive = self.root / "archive"
        self.archive.mkdir()
        self.root_patch = patch.object(database, "root_dir", return_value=self.root)
        self.archive_patch = patch.object(
            database,
            "archive_root",
            return_value=self.archive,
        )
        self.root_patch.start()
        self.archive_patch.start()
        init_database(self.root / "invoice_archive.db")

    def tearDown(self) -> None:
        self.archive_patch.stop()
        self.root_patch.stop()
        self.temporary.cleanup()

    def _approve(self, record_id: str, document: dict):
        source = self.root / f"{record_id}.pdf"
        source.write_bytes(b"representative original invoice")
        record = {
            "id": record_id,
            "stored_file": str(source),
            "queue_status": "ready",
            "document": document,
        }
        result = InvoiceWorkflowService().approve(record, document)
        self.assertTrue(result.success, result.message)
        return result

    @staticmethod
    def _document(*, supplier: str, number: str, items: list[dict]) -> dict:
        return {
            "document_type": "חשבונית מס",
            "supplier": supplier,
            "supplier_id": f"vat-{number}",
            "invoice_number": number,
            "invoice_date": "2026-08-10",
            "subtotal": 921.18,
            "taxable_amount": 921.18,
            "vat_rate": 18.0,
            "vat": 165.81,
            "total": 1086.99,
            "tax_treatment": "חייב במע״מ",
            "currency": "ILS",
            "confidence": 0.99,
            "machine_issues": [],
            "model_notes": [],
            "items": items,
        }

    def test_delivery_terms_classify_as_delivery(self):
        for description in (
            "הובלה לבית לקוח",
            "הובלה",
            "משלוח",
            "דמי משלוח",
            "Shipping",
            "Delivery",
            "Freight",
        ):
            with self.subTest(description=description):
                self.assertEqual(
                    classify_invoice_line(description),
                    SemanticLineType.DELIVERY.value,
                )

    def test_small_semantic_taxonomy_handles_non_product_charges(self):
        self.assertEqual(
            classify_invoice_line("התקנה מקצועית"),
            SemanticLineType.SERVICE.value,
        )
        self.assertEqual(
            classify_invoice_line("דמי טיפול"),
            SemanticLineType.FEE.value,
        )
        self.assertEqual(
            classify_invoice_line("הנחה"),
            SemanticLineType.DISCOUNT_OR_ADJUSTMENT.value,
        )
        self.assertEqual(
            classify_invoice_line("מקפיא", line_total=-50),
            SemanticLineType.DISCOUNT_OR_ADJUSTMENT.value,
        )
        self.assertEqual(
            classify_invoice_line(""),
            SemanticLineType.UNKNOWN.value,
        )
        self.assertEqual(
            classify_invoice_line("unrecognized unpriced line"),
            SemanticLineType.UNKNOWN.value,
        )
        self.assertEqual(
            classify_invoice_line("מקפיאים - I-TECH - IT-CF244"),
            SemanticLineType.PRODUCT.value,
        )
        self.assertEqual(
            classify_invoice_line("מפצל לאל פסק"),
            SemanticLineType.PRODUCT.value,
        )

    def test_zabilo_mixed_invoice_learns_only_the_freezer(self):
        document = self._document(
            supplier='זבילו בע"מ',
            number="SI266003861",
            items=[
                {
                    "description": "הובלה לבית לקוח",
                    "quantity": 1,
                    "unit": "unit",
                    "unit_price": 168.64,
                    "line_total": 168.64,
                },
                {
                    "description": "מקפיאים - I-TECH - IT-CF244",
                    "quantity": 1,
                    "unit": "unit",
                    "unit_price": 752.54,
                    "line_total": 752.54,
                },
            ],
        )
        before = capture_learning_snapshot()
        result = self._approve("zabilo", document)
        after = capture_learning_snapshot()

        stored_items = invoice_items(int(result.invoice_id))
        self.assertEqual(len(stored_items), 2)
        self.assertEqual(
            dict(zip(stored_items["description"], stored_items["line_type"])),
            {
                "הובלה לבית לקוח": SemanticLineType.DELIVERY.value,
                "מקפיאים - I-TECH - IT-CF244": SemanticLineType.PRODUCT.value,
            },
        )
        with connect() as connection:
            invoice = connection.execute(
                "SELECT total, vat FROM invoices WHERE id = ?",
                (result.invoice_id,),
            ).fetchone()
            comparable_prices = connection.execute(
                "SELECT COUNT(*) FROM comparable_price_facts"
            ).fetchone()[0]
        self.assertEqual(invoice["total"], 1086.99)
        self.assertEqual(invoice["vat"], 165.81)
        self.assertEqual(comparable_prices, 1)

        memory = business_memory_data()
        self.assertEqual(memory["invoice_count"], 1)
        self.assertEqual(memory["supplier_count"], 1)
        self.assertEqual(memory["product_count"], 1)
        self.assertEqual(memory["price_point_count"], 1)
        self.assertEqual(memory["recent"].iloc[0]["product_count"], 1)
        self.assertEqual(after.invoices - before.invoices, 1)
        self.assertEqual(after.suppliers - before.suppliers, 1)
        self.assertEqual(after.products - before.products, 1)
        self.assertEqual(after.comparable_prices - before.comparable_prices, 1)
        self.assertEqual(
            product_memory_options(),
            ["מקפיאים - I-TECH - IT-CF244"],
        )

        repeated_source = self.root / "repeat-zabilo.pdf"
        repeated_source.write_bytes(b"representative original invoice")
        reused = approved_document_for_identical_source(
            repeated_source,
            "zabilo.pdf",
        )
        self.assertIsNotNone(reused)
        self.assertEqual(len(reused["items"]), 2)
        self.assertEqual(
            {item["description"] for item in reused["items"]},
            {"הובלה לבית לקוח", "מקפיאים - I-TECH - IT-CF244"},
        )

        accountant = accountant_month_status("2026-08")
        package = zipfile.ZipFile(io.BytesIO(build_accountant_package(accountant)))
        self.assertTrue(any(name.startswith("invoices/") for name in package.namelist()))

    def test_aker_product_remains_product_and_creates_price_fact(self):
        document = self._document(
            supplier="אקר מחשבים",
            number="257940",
            items=[{
                "description": "מפצל לאל פסק",
                "quantity": 1,
                "unit": "unit",
                "unit_price": 120.0,
                "line_total": 120.0,
            }],
        )
        result = self._approve("aker", document)

        stored = invoice_items(int(result.invoice_id)).iloc[0]
        self.assertEqual(stored["line_type"], SemanticLineType.PRODUCT.value)
        self.assertEqual(
            [product.canonical_name for product in BusinessIdentityRepository().products()],
            ["מפצל לאל פסק"],
        )
        facts = ComparablePriceLedger().facts_for_invoice(int(result.invoice_id))
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].canonical_product_name, "מפצל לאל פסק")

    def test_legacy_false_product_is_readable_but_fails_closed(self):
        with connect() as connection:
            invoice_id = connection.execute(
                """INSERT INTO invoices(
                       file_name, archived_path, supplier, supplier_id,
                       invoice_number, invoice_date, document_type, total, vat,
                       currency, status, created_at, approved_at, updated_at
                   ) VALUES ('legacy.pdf', '', 'Legacy', 'legacy-vat', '1',
                             '2026-08-01', 'חשבונית מס', 168.64, 0,
                             'ILS', 'approved', '2026-08-01', '2026-08-01',
                             '2026-08-01')"""
            ).lastrowid
            connection.execute(
                """INSERT INTO invoice_items(
                       invoice_id, description, quantity, unit, unit_price,
                       line_total, line_type
                   ) VALUES (?, 'הובלה לבית לקוח', 1, 'unit', 168.64,
                             168.64, 'product')""",
                (invoice_id,),
            )

        rows = invoice_items(int(invoice_id))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.iloc[0]["description"], "הובלה לבית לקוח")
        self.assertFalse(classify_invoice_item(rows.iloc[0].to_dict()) == "product")
        self.assertEqual(BusinessIdentityRepository().identity_health()["products"], 0)
        self.assertEqual(ComparablePriceLedger().sync()["facts"], 0)
        self.assertEqual(
            classify_invoice_item({"description": "", "line_type": ""}),
            SemanticLineType.UNKNOWN.value,
        )


if __name__ == "__main__":
    unittest.main()
