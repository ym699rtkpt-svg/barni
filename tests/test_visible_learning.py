from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from services.product_state import FirstFeedState
from services.visible_learning import (
    LearningSnapshot,
    capture_learning_snapshot,
    learning_change,
)


class _Ledger:
    def __init__(self, trusted_count: int) -> None:
        self.trusted_count = trusted_count

    def trusted_observations(self, *, ensure: bool = True):
        self.ensure = ensure
        return [object()] * self.trusted_count


class VisibleLearningTests(unittest.TestCase):
    def test_first_time_business_requires_onboarding(self):
        with tempfile.TemporaryDirectory() as folder:
            state = FirstFeedState(Path(folder) / "product-state.json")
            self.assertTrue(state.onboarding_required(approved_invoice_count=0))

    def test_returning_business_is_not_forced_through_onboarding(self):
        with tempfile.TemporaryDirectory() as folder:
            state = FirstFeedState(Path(folder) / "product-state.json")
            self.assertFalse(state.onboarding_required(approved_invoice_count=3))
            self.assertTrue(state.is_complete())

    def test_approved_first_invoice_completes_and_persists_after_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "product-state.json"
            FirstFeedState(path).complete(
                invoice_id=41,
                completed_at=datetime(2026, 8, 10, 9, 30),
            )
            restarted = FirstFeedState(path)
            self.assertTrue(restarted.is_complete())
            self.assertFalse(restarted.onboarding_required(approved_invoice_count=1))

    def test_failed_extraction_does_not_complete_onboarding(self):
        with tempfile.TemporaryDirectory() as folder:
            state = FirstFeedState(Path(folder) / "product-state.json")
            self.assertTrue(state.onboarding_required(approved_invoice_count=0))
            self.assertFalse(state.is_complete())

    def test_learning_values_come_from_memory_and_trusted_price_facts(self):
        before = capture_learning_snapshot(
            memory_provider=lambda: {
                "invoice_count": 2, "supplier_count": 1, "product_count": 4,
            },
            price_ledger=_Ledger(2),
        )
        after = capture_learning_snapshot(
            memory_provider=lambda: {
                "invoice_count": 3, "supplier_count": 2, "product_count": 7,
            },
            price_ledger=_Ledger(4),
        )

        change = learning_change(before, after)

        self.assertEqual(change.invoices, 1)
        self.assertEqual(change.suppliers, 1)
        self.assertEqual(change.products, 3)
        self.assertEqual(change.comparable_prices, 2)

    def test_zero_value_learning_rows_are_hidden(self):
        change = learning_change(
            LearningSnapshot(invoices=1, suppliers=1, products=4, comparable_prices=2),
            LearningSnapshot(invoices=2, suppliers=1, products=6, comparable_prices=2),
        )
        self.assertEqual(change.visible_rows(), ((2, "products"),))


if __name__ == "__main__":
    unittest.main()
