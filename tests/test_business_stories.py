from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import init_database
from services.business_stories import BusinessStoryEngine, StoryContext


class BusinessStoryEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "stories.db"
        init_database(self.path)

        def factory():
            connection = sqlite3.connect(self.path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            return connection

        self.connect = factory
        self.engine = BusinessStoryEngine(factory)

    def tearDown(self):
        self.temp.cleanup()

    def _invoice(self, invoice_id: int, date: str, number: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO invoices(
                       id, file_name, archived_path, supplier, supplier_id,
                       invoice_number, invoice_date, document_type, currency,
                       subtotal, vat, total, tax_treatment, status,
                       created_at, approved_at, updated_at
                   ) VALUES (?, ?, ?, 'Tnuva', '515151515', ?, ?, 'Invoice',
                             'ILS', 100, 17, 117, 'חייב במע״מ', 'approved', ?, ?, ?)""",
                (invoice_id, f"{invoice_id}.pdf", f"/{invoice_id}.pdf", number, date, date, date, date),
            )

    def _item(self, item_id: int, invoice_id: int, price: float, unit: str = "l") -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO invoice_items(
                       id, invoice_id, description, quantity, unit, unit_price,
                       line_total, line_type
                   ) VALUES (?, ?, 'Olive oil', 2, ?, ?, ?, 'product')""",
                (item_id, invoice_id, unit, price, price * 2),
            )

    def test_trusted_price_story_links_both_invoices(self):
        self._invoice(1, "2026-08-01", "841")
        self._invoice(2, "2026-08-08", "852")
        self._item(1, 1, 42)
        self._item(2, 2, 48)

        stories = self.engine.generate(StoryContext(current_invoice_id=2), max_stories=1)

        self.assertEqual(stories[0].story_type, "price_increase")
        self.assertIn("14.3%", stories[0].description)
        self.assertEqual([value.invoice_id for value in stories[0].evidence], [1, 2])
        self.assertEqual(stories[0].evidence_values["fact_status"], "TRUSTED")

    def test_untrusted_price_never_becomes_price_story(self):
        self._invoice(1, "2026-08-01", "841")
        self._invoice(2, "2026-08-08", "852")
        self._item(1, 1, 42, "unknown")
        self._item(2, 2, 48, "unknown")

        stories = self.engine.generate(StoryContext(current_invoice_id=2), max_stories=3)

        self.assertFalse(any(story.category == "price" for story in stories))
        self.assertTrue(any(story.story_type == "identity_review_needed" for story in stories))

    def test_approval_memory_story_uses_current_invoice_as_evidence(self):
        self._invoice(1, "2026-08-08", "841")
        self._item(1, 1, 42)

        story = self.engine.generate(
            StoryContext(current_invoice_id=1, memory_delta={"suppliers": 1}),
            max_stories=1,
        )[0]

        self.assertEqual(story.story_type, "supplier_learned")
        self.assertEqual(story.evidence[0].invoice_id, 1)

    def test_since_story_summarizes_only_approved_evidence(self):
        self._invoice(1, "2026-08-08", "841")
        self._item(1, 1, 42)

        stories = self.engine.generate(
            StoryContext(since="2026-08-08"),
            max_stories=5,
        )

        learned = next(story for story in stories if story.story_type == "invoices_learned")
        self.assertEqual(learned.description, "Barni successfully learned 1 invoice.")
        self.assertEqual(learned.evidence[0].invoice_id, 1)


if __name__ == "__main__":
    unittest.main()
