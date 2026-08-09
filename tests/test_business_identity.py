from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import init_database
from services.business_identity import (
    BusinessIdentityRepository,
    normalize_identity_text,
    normalize_packaging,
    normalize_unit,
)


class BusinessIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "identity.db"
        init_database(self.path)

        def connection_factory():
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            return connection

        self.repository = BusinessIdentityRepository(connection_factory)

    def tearDown(self):
        self.temp.cleanup()

    def _invoice(self, invoice_id: int, supplier: str, vat_id: str) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO invoices (
                    id, file_name, archived_path, supplier, supplier_id,
                    created_at, approved_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, '2026-08-09', '2026-08-09', '2026-08-09')
                """,
                (invoice_id, f"{invoice_id}.pdf", f"/{invoice_id}.pdf", supplier, vat_id),
            )

    def _item(self, item_id: int, invoice_id: int, description: str, unit: str) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO invoice_items (
                    id, invoice_id, description, unit, unit_price, line_type
                ) VALUES (?, ?, ?, ?, 10, 'product')
                """,
                (item_id, invoice_id, description, unit),
            )

    def test_supplier_aliases_share_identity_when_vat_id_matches(self):
        self._invoice(1, "Supplier Ltd.", "51-515151-5")
        self._invoice(2, "SUPPLIER LTD", "515151515")

        self.repository.sync_existing_memory()
        suppliers = self.repository.suppliers()

        self.assertEqual(len(suppliers), 1)
        self.assertEqual(set(suppliers[0].aliases), {"Supplier Ltd.", "SUPPLIER LTD"})

    def test_products_merge_only_after_explicit_confirmation(self):
        self._invoice(1, "Supplier", "1")
        self._item(1, 1, "Olive Oil 1 L", "unit")
        self._item(2, 1, "Olive oil one litre", "unit")
        self.repository.sync_existing_memory()
        products = self.repository.products()
        self.assertEqual(len(products), 2)

        self.repository.merge_products(products[1].id, products[0].id)
        merged = self.repository.products()

        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged[0].aliases), 2)

    def test_unit_and_packaging_normalization_is_conservative(self):
        self.assertEqual(normalize_unit('ק״ג'), "kg")
        self.assertEqual(normalize_unit("mystery crate"), "mysterycrate")
        package = normalize_packaging("Olive oil 750 ml")
        self.assertEqual(package.quantity, 750.0)
        self.assertEqual(package.unit, "ml")

    def test_evidence_resolves_to_source_invoice(self):
        self._invoice(1, "Supplier Ltd.", "515151515")
        self.repository.sync_existing_memory()

        evidence = self.repository.resolve_evidence((1, "current-queue"))

        self.assertEqual(evidence[0].invoice_id, 1)
        self.assertEqual(evidence[0].supplier, "Supplier Ltd.")
        self.assertEqual(evidence[1].source_record_id, "current-queue")
        self.assertIsNone(evidence[1].invoice_id)

    def test_queue_identifier_cannot_overflow_invoice_evidence_lookup(self):
        queue_id = "202608091234567890123456789"

        evidence = self.repository.resolve_evidence((queue_id,))

        self.assertEqual(evidence[0].source_record_id, queue_id)
        self.assertIsNone(evidence[0].invoice_id)

    def test_identity_normalization_handles_hebrew_punctuation(self):
        self.assertEqual(
            normalize_identity_text('מגבוני סיון בע״מ'),
            normalize_identity_text('מגבוני  סיון בע"מ'),
        )


if __name__ == "__main__":
    unittest.main()
