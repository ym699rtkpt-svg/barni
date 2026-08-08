from __future__ import annotations

import unittest

import pandas as pd

from smart_archive import _search_summary


class SearchExperienceTests(unittest.TestCase):
    def test_empty_summary_is_calm(self):
        self.assertEqual(
            _search_summary("milk", pd.DataFrame(), [], []),
            "I couldn't find any matching invoices.",
        )

    def test_exact_supplier_summary_names_supplier(self):
        results = pd.DataFrame([
            {"supplier": "Tnuva"},
            {"supplier": "Tnuva"},
            {"supplier": "Other"},
        ])
        self.assertEqual(
            _search_summary("tnuva", results, ["Tnuva"], []),
            "I found 2 invoices from Tnuva.",
        )

    def test_product_summary_counts_purchases(self):
        results = pd.DataFrame([{"supplier": "Tnuva"}])
        products = [
            {"purchases": [{}, {}]},
            {"purchases": [{}]},
        ]
        self.assertEqual(
            _search_summary("milk", results, [], products),
            "I found 3 milk purchases.",
        )

    def test_generic_summary_counts_matching_invoices(self):
        results = pd.DataFrame([{"supplier": "A"}, {"supplier": "B"}])
        self.assertEqual(
            _search_summary("July invoices", results, [], []),
            "I found 2 invoices matching your search.",
        )


if __name__ == "__main__":
    unittest.main()
