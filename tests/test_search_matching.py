from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from database import (
    init_database,
    insert_invoice,
    search_invoices,
    search_suggestion_rows,
)
from services.business_identity import BusinessIdentityRepository
from services.search_matching import (
    build_search_suggestions,
    contains_search_match,
    prefix_search_match,
    search_suggestion_catalog,
)


class SearchMatchingTests(unittest.TestCase):
    def test_multilingual_contains_and_transliteration(self):
        self.assertTrue(contains_search_match("תנובה", "tnuva"))
        self.assertTrue(contains_search_match("Milk 3%", "מילק"))
        self.assertTrue(contains_search_match("Kitchenware", "chenw"))
        self.assertTrue(contains_search_match("חשבונית 841", "בוני"))
        self.assertFalse(contains_search_match("Milk", "tomato"))

    def test_one_character_is_prefix_and_two_characters_are_contains(self):
        rows = [{
            "invoice_id": 7,
            "supplier": "Tnuva",
            "invoice_number": "INV-841",
            "invoice_date": "2026-08-09",
            "document_type": "Invoice",
            "description": "Milk 3%",
            "canonical_product_name": "Milk 3%",
            "item_code": "MILK-3",
        }]

        one_character = build_search_suggestions("i", rows)
        two_characters = build_search_suggestions("il", rows)

        self.assertTrue(one_character)
        self.assertTrue(all(prefix_search_match(item.label, "i") for item in one_character))
        self.assertTrue(any(item.kind == "Product" and item.label == "Milk 3%" for item in two_characters))

    def test_suggestion_types_resolve_directly_to_the_source_invoice(self):
        rows = [{
            "invoice_id": 7,
            "supplier": "Tnuva 2026",
            "invoice_number": "INV-2026",
            "invoice_date": "2026-08-09",
            "document_type": "Invoice",
            "description": "Milk 2026",
            "canonical_product_name": "Milk 2026",
            "item_code": "MILK-2026",
        }]
        suggestions = [
            *build_search_suggestions("tn", rows),
            *build_search_suggestions("milk", rows),
            *build_search_suggestions("2026", rows, limit=20),
        ]

        self.assertEqual(
            {"Supplier", "Product", "Invoice", "Invoice number", "Date"},
            {item.kind for item in suggestions},
        )
        self.assertTrue(all(item.invoice_id == 7 for item in suggestions))

    def test_real_hebrew_memory_prefixes_and_product_contains(self):
        rows = [
            {
                "invoice_id": 1,
                "canonical_supplier_name": "אקר מחשבים",
                "invoice_number": "257940",
                "invoice_date": "2026-08-01",
                "canonical_product_name": "מפצל לאל פסק",
            },
            {
                "invoice_id": 2,
                "canonical_supplier_name": 'זבילו בע"מ',
                "invoice_number": "SI266003861",
                "invoice_date": "2026-08-02",
                "canonical_product_name": "מקפיאים - I-TECH - IT-CF244",
            },
        ]

        self.assertIn(
            "אקר מחשבים",
            [item.label for item in build_search_suggestions("א", rows)],
        )
        self.assertIn(
            'זבילו בע"מ',
            [item.label for item in build_search_suggestions("ז", rows)],
        )
        self.assertIn(
            "מפצל לאל פסק",
            [item.label for item in build_search_suggestions("מפ", rows)],
        )
        for query in ("I-TECH", "מקפ"):
            self.assertIn(
                "מקפיאים - I-TECH - IT-CF244",
                [item.label for item in build_search_suggestions(query, rows)],
            )

    def test_catalog_uses_canonical_products_only(self):
        rows = [
            {
                "invoice_id": 1,
                "canonical_supplier_name": "Supplier",
                "description": "הובלה לבית לקוח",
                "canonical_product_name": "",
            },
            {
                "invoice_id": 1,
                "canonical_supplier_name": "Supplier",
                "description": "מפצל לאל פסק",
                "canonical_product_name": "מפצל לאל פסק",
            },
        ]

        catalog = search_suggestion_catalog(rows)
        product_labels = [item.label for item in catalog if item.kind == "Product"]
        self.assertEqual(product_labels, ["מפצל לאל פסק"])
        self.assertNotIn("הובלה לבית לקוח", product_labels)


class DatabaseSearchMatchingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.archive = self.root / "archive"
        self.archive.mkdir()
        self.root_patch = patch.object(database, "root_dir", return_value=self.root)
        self.archive_patch = patch.object(database, "archive_root", return_value=self.archive)
        self.root_patch.start()
        self.archive_patch.start()
        init_database(self.root / "invoice_archive.db")

    def tearDown(self) -> None:
        self.archive_patch.stop()
        self.root_patch.stop()
        self.temporary.cleanup()

    def test_database_free_text_reuses_multilingual_matcher(self):
        source = self.root / "source.pdf"
        source.write_bytes(b"invoice")
        invoice_id = insert_invoice(source, {
            "document_type": "חשבונית מס",
            "supplier": "תנובה",
            "invoice_number": "841",
            "invoice_date": "2026-08-09",
            "total": 100,
            "items": [{
                "description": "מילק 3%",
                "quantity": 1,
                "unit_price": 10,
                "line_total": 10,
            }],
        })

        supplier_results = search_invoices(free_text="tnuva", statuses=["approved"])
        product_results = search_invoices(free_text="milk", statuses=["approved"])

        self.assertEqual(supplier_results["id"].tolist(), [invoice_id])
        self.assertEqual(product_results["id"].tolist(), [invoice_id])

    def test_database_catalog_excludes_delivery_from_product_suggestions(self):
        source = self.root / "mixed.pdf"
        source.write_bytes(b"invoice")
        insert_invoice(source, {
            "document_type": "חשבונית מס",
            "supplier": 'זבילו בע"מ',
            "supplier_id": "zabilo-vat",
            "invoice_number": "SI266003861",
            "invoice_date": "2026-08-09",
            "total": 1000,
            "items": [
                {
                    "description": "הובלה לבית לקוח",
                    "quantity": 1,
                    "unit_price": 168.64,
                    "line_total": 168.64,
                },
                {
                    "description": "מקפיאים - I-TECH - IT-CF244",
                    "quantity": 1,
                    "unit_price": 752.54,
                    "line_total": 752.54,
                },
            ],
        })
        BusinessIdentityRepository().sync_existing_memory()

        catalog = search_suggestion_catalog(search_suggestion_rows())
        product_labels = [item.label for item in catalog if item.kind == "Product"]
        self.assertIn("מקפיאים - I-TECH - IT-CF244", product_labels)
        self.assertNotIn("הובלה לבית לקוח", product_labels)


if __name__ == "__main__":
    unittest.main()
