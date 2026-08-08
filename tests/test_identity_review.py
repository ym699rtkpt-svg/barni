from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import init_database
from services.business_identity import BusinessIdentityRepository
from services.identity_review import IdentityReviewService


class IdentityReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "review.db"
        init_database(self.path)

        def connection_factory():
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            return connection

        self.identities = BusinessIdentityRepository(connection_factory)
        self.reviews = IdentityReviewService(connection_factory, self.identities)
        with connection_factory() as connection:
            for invoice_id, date in ((1, "2026-08-01"), (2, "2026-08-05")):
                connection.execute(
                    """INSERT INTO invoices(
                           id, file_name, archived_path, supplier, supplier_id,
                           invoice_number, invoice_date, currency, created_at, approved_at, updated_at
                       ) VALUES (?, ?, ?, 'Kitchen Supplier', '515151515', ?, ?, 'ILS', ?, ?, ?)""",
                    (invoice_id, f"{invoice_id}.pdf", f"/{invoice_id}.pdf", str(invoice_id), date, date, date, date),
                )
            connection.execute(
                """INSERT INTO invoice_items(id, invoice_id, description, quantity, unit, unit_price, line_type)
                   VALUES (1, 1, 'Olive Oil 1L', 1, 'unit', 42, 'product')"""
            )
            connection.execute(
                """INSERT INTO invoice_items(id, invoice_id, description, quantity, unit, unit_price, line_type)
                   VALUES (2, 2, 'Olive Oil 1 L', 1, 'unit', 43, 'product')"""
            )
            connection.commit()
        self.identities.sync_existing_memory()

    def tearDown(self):
        self.temp.cleanup()

    def _product_match(self):
        return next(value for value in self.reviews.pending(10) if value.review_type == "product_match")

    def test_candidate_is_evidence_backed_and_prioritized(self):
        candidate = self._product_match()
        self.assertGreaterEqual(candidate.confidence, 0.74)
        self.assertEqual({source.invoice_id for source in candidate.evidence}, {1, 2})
        self.assertTrue(any("descriptions" in reason for reason in candidate.reasons))

    def test_confirm_merges_and_undo_restores_both_identities(self):
        candidate = self._product_match()
        decision_id = self.reviews.confirm(candidate.id)
        self.assertEqual(len(self.identities.products()), 1)

        self.identities.undo_decision(decision_id)
        products = self.identities.products()
        self.assertEqual(len(products), 2)
        with sqlite3.connect(self.path) as connection:
            links = connection.execute(
                "SELECT canonical_product_id FROM invoice_item_identity_links ORDER BY item_id"
            ).fetchall()
        self.assertNotEqual(links[0][0], links[1][0])

    def test_rejected_match_does_not_return_to_queue(self):
        candidate = self._product_match()
        self.reviews.reject(candidate.id)
        self.reviews.refresh_queue()
        self.assertNotIn(candidate.id, [value.id for value in self.reviews.pending(20)])

    def test_split_and_undo_preserve_source_records(self):
        products = self.identities.products()
        merged_id = self.identities.merge_products(products[1].id, products[0].id)
        canonical_id = self.identities.products()[0].id
        split_decision = self.identities.split_identity(
            "product", canonical_id, [2], "Olive Oil 1 L",
        )
        self.assertEqual(len(self.identities.products()), 2)
        self.identities.undo_decision(split_decision)
        self.assertEqual(len(self.identities.products()), 1)
        self.identities.undo_decision(merged_id)
        self.assertEqual(len(self.identities.products()), 2)

    def test_decision_records_actor_reason_evidence_and_time(self):
        candidate = self._product_match()
        decision_id = self.reviews.confirm(candidate.id, actor="Restaurant owner")
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM identity_decisions WHERE id = ?", (decision_id,)
            ).fetchone()
        self.assertEqual(row["actor"], "Restaurant owner")
        self.assertTrue(row["reason"])
        self.assertIn("invoice_ids", row["evidence_json"])
        self.assertTrue(row["decided_at"])

    def test_conflicting_barcodes_veto_a_product_match(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """INSERT INTO invoice_items(id, invoice_id, description, quantity, unit, unit_price, line_type)
                   VALUES (3, 1, 'Frozen Fish Barcode 7290001906125', 1, 'kg', 40, 'product')"""
            )
            connection.execute(
                """INSERT INTO invoice_items(id, invoice_id, description, quantity, unit, unit_price, line_type)
                   VALUES (4, 2, 'Frozen Fish Barcode 7290001906194', 1, 'kg', 41, 'product')"""
            )
            connection.commit()
        self.identities.sync_existing_memory()
        matches = self.reviews.pending(30)
        pairs = {(candidate.source_name, candidate.target_name) for candidate in matches}
        self.assertNotIn(
            ("Frozen Fish Barcode 7290001906125", "Frozen Fish Barcode 7290001906194"),
            pairs,
        )


if __name__ == "__main__":
    unittest.main()
