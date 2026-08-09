from __future__ import annotations

import sqlite3
import json
from datetime import datetime
import tempfile
import unittest
from pathlib import Path

from database import init_database
from services.business_stories import BusinessStoryEngine, StoryContext
from services.feed_journal import FeedJournalCursor


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

    def test_feed_uses_approved_memory_and_orders_newest_invoice_first(self):
        self._invoice(1, "2026-08-01", "841")
        self._invoice(2, "2026-08-08", "852")
        self._item(1, 1, 42)
        self._item(2, 2, 42)

        stories = self.engine.generate_feed(
            StoryContext(since="2026-08-01"),
            max_stories=10,
        )

        self.assertEqual(stories[0].story_type, "invoice_approved")
        self.assertEqual(stories[0].evidence[0].invoice_id, 2)
        self.assertTrue(any(story.story_type == "supplier_learned" for story in stories))
        repeated = next(story for story in stories if story.story_type == "product_seen_again")
        self.assertEqual(repeated.evidence_values["purchase_count"], 2)
        self.assertEqual({source.invoice_id for source in repeated.evidence}, {1, 2})

    def test_feed_duplicate_resolution_uses_completed_operation_evidence(self):
        self._invoice(1, "2026-08-08", "841")
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO invoice_approval_operations(
                       operation_key, operation_status, duplicate_resolution,
                       outcome, invoice_id, created_at, updated_at, completed_at
                   ) VALUES ('duplicate-1', 'completed', 'replace', 'replaced', 1,
                             '2026-08-08', '2026-08-08', '2026-08-08')"""
            )

        stories = self.engine.generate_feed(StoryContext(since="2026-08-08"), max_stories=10)
        duplicate = next(story for story in stories if story.story_type == "duplicate_resolved")

        self.assertEqual(duplicate.evidence[0].invoice_id, 1)
        self.assertIn("replaced", duplicate.description.lower())

    def test_feed_identity_completion_requires_source_invoice_evidence(self):
        self._invoice(1, "2026-08-08", "841")
        self._item(1, 1, 42)
        self.engine.ledger.sync()
        with self.connect() as connection:
            supplier_id = connection.execute("SELECT id FROM canonical_suppliers").fetchone()[0]
            connection.execute(
                """INSERT INTO identity_decisions(
                       entity_type, source_canonical_id, target_canonical_id,
                       decision_type, alias, decided_at, evidence_json
                   ) VALUES ('supplier', ?, ?, 'merge', 'Tnuva alias',
                             '2026-08-08', ?)""",
                (supplier_id, supplier_id, json.dumps({"invoice_ids": [1]})),
            )

        stories = self.engine.generate_feed(StoryContext(since="2026-08-08"), max_stories=10)
        identity = next(
            story for story in stories if story.story_type == "identity_review_completed"
        )

        self.assertEqual(identity.evidence[0].invoice_id, 1)
        self.assertIn("Tnuva", identity.description)

    def test_feed_visit_cursor_is_durable_and_recovers_backup(self):
        cursor = FeedJournalCursor(Path(self.temp.name) / "feed-journal.json")
        first = datetime(2026, 8, 8, 7, 30)
        second = datetime(2026, 8, 9, 8, 15)
        cursor.mark_visited(first)
        cursor.mark_visited(second)

        self.assertEqual(cursor.previous_visit(), second.isoformat(timespec="seconds"))
        cursor.path.write_text("{broken", encoding="utf-8")
        self.assertEqual(cursor.previous_visit(), first.isoformat(timespec="seconds"))


if __name__ == "__main__":
    unittest.main()
