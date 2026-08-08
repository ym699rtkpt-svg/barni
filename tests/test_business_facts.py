from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import init_database
from services.business_facts import BusinessFactsEngine, ComparablePriceLedger, FactStatus
from services.business_identity import BusinessIdentityRepository


class BusinessFactsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "facts.db"
        init_database(self.path)

        def connection_factory():
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            return connection

        self.connect = connection_factory
        self.identities = BusinessIdentityRepository(connection_factory)
        self.engine = BusinessFactsEngine(connection_factory)
        self.ledger = ComparablePriceLedger(connection_factory)

    def tearDown(self):
        self.temp.cleanup()

    def _invoice(
        self, invoice_id: int, *, currency: str = "ILS", subtotal: float = 100,
        vat: float = 17, total: float = 117, document_type: str = "Invoice",
        tax_treatment: str = "חייב במע״מ",
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO invoices(
                       id, file_name, archived_path, supplier, supplier_id,
                       invoice_number, invoice_date, document_type, currency,
                       subtotal, vat, total, tax_treatment,
                       created_at, approved_at, updated_at
                   ) VALUES (?, ?, ?, 'Supplier', '515151515', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    invoice_id, f"{invoice_id}.pdf", f"/{invoice_id}.pdf", str(invoice_id),
                    f"2026-08-{invoice_id:02d}", document_type, currency,
                    subtotal, vat, total, tax_treatment,
                    "2026-08-09", "2026-08-09", "2026-08-09",
                ),
            )

    def _item(self, item_id: int, invoice_id: int, description: str, unit: str, price, quantity=1):
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO invoice_items(
                       id, invoice_id, description, quantity, unit, unit_price,
                       line_total, line_type
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, 'product')""",
                (item_id, invoice_id, description, quantity, unit, price, price),
            )

    def test_same_product_prices_are_trusted_and_explainable(self):
        self._invoice(1); self._invoice(2)
        self._item(1, 1, "Olive Oil", "unit", 42)
        self._item(2, 2, "Olive Oil", "unit", 48)
        self.engine.sync()

        facts = self.ledger.facts_for_invoice(2, ensure=False)
        comparison = self.ledger.previous_comparable(facts[0])

        self.assertEqual(facts[0].fact.trust_status, FactStatus.TRUSTED)
        self.assertTrue(comparison.comparable)
        self.assertAlmostEqual(comparison.change_pct, 14.2857, places=3)
        self.assertEqual(comparison.evidence_invoice_ids, (1, 2))
        self.assertEqual(facts[0].fact.confidence["product_identity"], 1.0)

    def test_different_packages_normalize_to_same_litre_basis(self):
        self._invoice(1); self._invoice(2)
        self._item(1, 1, "Milk 500 ml", "unit", 5)
        self._item(2, 2, "Milk 1 l", "unit", 9)
        self.identities.sync_existing_memory()
        products = self.identities.products()
        self.identities.merge_products(products[1].id, products[0].id)
        self.engine.sync()

        current = self.ledger.facts_for_invoice(2, ensure=False)[0]
        comparison = self.ledger.previous_comparable(current)
        self.assertEqual(current.normalized_unit, "l")
        self.assertAlmostEqual(current.normalized_price, 9)
        self.assertAlmostEqual(comparison.previous.normalized_price, 10)
        self.assertTrue(comparison.comparable)

    def test_incompatible_units_reject_comparison(self):
        self._invoice(1); self._invoice(2)
        self._item(1, 1, "Rice", "kg", 10)
        self._item(2, 2, "Rice", "unit", 10)
        self.engine.sync()
        first = self.ledger.facts_for_invoice(1, ensure=False)[0]
        second = self.ledger.facts_for_invoice(2, ensure=False)[0]
        comparison = self.ledger.compare(second, first)
        self.assertFalse(comparison.comparable)
        self.assertEqual(comparison.status, FactStatus.UNIT_CONFLICT)

    def test_lines_on_same_invoice_are_not_historical_comparisons(self):
        self._invoice(1)
        self._item(1, 1, "Electricity", "unit", 10)
        self._item(2, 1, "Electricity", "unit", 12)
        self.engine.sync()
        facts = self.ledger.facts_for_invoice(1, ensure=False)
        comparison = self.ledger.compare(facts[1], facts[0])
        self.assertFalse(comparison.comparable)
        self.assertEqual(comparison.status, FactStatus.NOT_COMPARABLE)
        self.assertIn("same invoice", comparison.explanation)

    def test_vat_conflict_is_not_comparable_and_enters_review(self):
        self._invoice(1, subtotal=100, vat=17, total=105)
        self._item(1, 1, "Oil", "unit", 10)
        self.engine.sync()
        fact = self.ledger.facts_for_invoice(1, ensure=False)[0]
        self.assertEqual(fact.fact.trust_status, FactStatus.VAT_CONFLICT)
        with self.connect() as connection:
            queued = connection.execute(
                "SELECT COUNT(*) FROM identity_review_candidates WHERE review_type = 'fact_vat_conflict' AND status = 'pending'"
            ).fetchone()[0]
        self.assertEqual(queued, 1)

    def test_credit_note_is_not_a_purchase_price(self):
        self._invoice(1, document_type="Credit Note", subtotal=-100, vat=-17, total=-117)
        self._item(1, 1, "Oil", "unit", 10)
        self.engine.sync()
        fact = self.ledger.facts_for_invoice(1, ensure=False)[0]
        self.assertEqual(fact.fact.trust_status, FactStatus.NOT_COMPARABLE)

    def test_currency_difference_rejects_pair_without_exchange_rate(self):
        self._invoice(1, currency="ILS"); self._invoice(2, currency="USD")
        self._item(1, 1, "Oil", "unit", 10)
        self._item(2, 2, "Oil", "unit", 3)
        self.engine.sync()
        first = self.ledger.facts_for_invoice(1, ensure=False)[0]
        second = self.ledger.facts_for_invoice(2, ensure=False)[0]
        comparison = self.ledger.compare(second, first)
        self.assertEqual(comparison.status, FactStatus.CURRENCY_CONFLICT)
        self.assertFalse(comparison.comparable)

    def test_missing_quantity_is_insufficient_data(self):
        self._invoice(1)
        self._item(1, 1, "Oil", "unit", 10, None)
        self.engine.sync()
        fact = self.ledger.facts_for_invoice(1, ensure=False)[0]
        self.assertEqual(fact.fact.trust_status, FactStatus.INSUFFICIENT_DATA)
        self.assertIn("quantity", fact.fact.status_explanation)

    def test_package_without_size_enters_review(self):
        self._invoice(1)
        self._item(1, 1, "Napkins", "package", 10)
        self.engine.sync()
        fact = self.ledger.facts_for_invoice(1, ensure=False)[0]
        self.assertEqual(fact.fact.trust_status, FactStatus.PACKAGE_CONFLICT)
        with self.connect() as connection:
            queued = connection.execute(
                "SELECT COUNT(*) FROM identity_review_candidates WHERE review_type = 'fact_package_conflict' AND status = 'pending'"
            ).fetchone()[0]
        self.assertEqual(queued, 1)


if __name__ == "__main__":
    unittest.main()
