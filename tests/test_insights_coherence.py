from __future__ import annotations

import inspect
import unittest

import pandas as pd

from enhanced_dashboard import (
    _has_spend_trend_evidence,
    _meaningful_category_data,
    _supplier_comparison_data,
    render_enhanced_dashboard,
)
from ui.business_memory import _has_meaningful_growth, _meaningful_categories


class InsightsCoherenceTests(unittest.TestCase):
    def test_one_month_is_not_presented_as_a_spend_trend(self):
        monthly = pd.DataFrame([{"month": "2026-08", "total": 300}])
        self.assertFalse(_has_spend_trend_evidence(monthly))

    def test_spend_trend_returns_with_two_distinct_months(self):
        monthly = pd.DataFrame([
            {"month": "2026-07", "total": 100},
            {"month": "2026-08", "total": 300},
        ])
        self.assertTrue(_has_spend_trend_evidence(monthly))

    def test_supplier_comparison_rejects_isolated_purchases(self):
        documents = pd.DataFrame([
            {"supplier": "A", "total": 100},
            {"supplier": "B", "total": 200},
        ])
        self.assertTrue(_supplier_comparison_data(documents).empty)

    def test_supplier_comparison_returns_for_two_repeat_suppliers(self):
        documents = pd.DataFrame([
            {"supplier": "A", "total": 100},
            {"supplier": "A", "total": 120},
            {"supplier": "B", "total": 200},
            {"supplier": "B", "total": 210},
            {"supplier": "One-off", "total": 900},
        ])
        comparison = _supplier_comparison_data(documents)
        self.assertEqual(comparison["supplier"].tolist(), ["B", "A"])
        self.assertNotIn("One-off", comparison["supplier"].tolist())

    def test_growth_requires_more_than_one_observation_date(self):
        same_day = pd.DataFrame([
            {"date": "2026-08-10", "Invoices": 2},
        ])
        progression = pd.DataFrame([
            {"date": "2026-08-09", "Invoices": 1},
            {"date": "2026-08-10", "Invoices": 2},
        ])
        self.assertFalse(_has_meaningful_growth(same_day))
        self.assertTrue(_has_meaningful_growth(progression))

    def test_uncategorized_majority_is_not_presented_as_category_insight(self):
        categories = pd.DataFrame([
            {"category": "לא מסווג", "count": 3},
            {"category": "Equipment", "count": 1},
        ])
        original = categories.copy(deep=True)
        self.assertTrue(_meaningful_categories(categories).empty)
        pd.testing.assert_frame_equal(categories, original)

        documents = pd.DataFrame([
            {"category": "לא מסווג", "subcategory": "", "total": 100},
            {"category": "לא מסווג", "subcategory": "", "total": 200},
        ])
        original_documents = documents.copy(deep=True)
        self.assertTrue(_meaningful_category_data(documents).empty)
        pd.testing.assert_frame_equal(documents, original_documents)

    def test_categorized_majority_returns_without_unknown_bucket(self):
        categories = pd.DataFrame([
            {"category": "Equipment", "count": 3},
            {"category": "לא מסווג", "count": 1},
        ])
        visible = _meaningful_categories(categories)
        self.assertEqual(visible["category"].tolist(), ["Equipment"])

    def test_each_insights_view_uses_its_own_evidence_rule(self):
        source = inspect.getsource(render_enhanced_dashboard)
        self.assertIn("_has_spend_trend_evidence(monthly)", source)
        self.assertIn("_supplier_comparison_data(documents)", source)
        self.assertNotIn("_has_meaningful_pattern_evidence", source)


if __name__ == "__main__":
    unittest.main()
