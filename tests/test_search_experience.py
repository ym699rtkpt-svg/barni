from __future__ import annotations

import ast
import inspect
import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from database import init_database, insert_invoice
from services.business_identity import BusinessIdentityRepository
from services.product_state import FirstFeedState
from smart_archive import (
    _format_memory_search_option,
    _memory_suggestions,
    _render_search_styles,
    _search_summary,
    render_database_archive,
)
from services.search_matching import SearchSuggestion


class SearchExperienceTests(unittest.TestCase):
    def test_search_header_sets_direct_lookup_scope(self):
        source = inspect.getsource(render_database_archive)
        self.assertIn(
            '"Search suppliers, products, invoices or dates."',
            source,
        )
        self.assertNotIn('"Find anything Barni remembers."', source)

    def test_search_input_has_idle_hover_and_focus_boundaries(self):
        styles = inspect.getsource(_render_search_styles)
        self.assertIn("border: 1px solid rgba(49, 91, 61, 0.24)", styles)
        self.assertIn('[data-baseweb="input"]:hover', styles)
        self.assertIn('[data-baseweb="input"]:focus-within', styles)
        self.assertIn("box-shadow: 0 0 0 2px", styles)

    def test_default_suggestions_remain_restrained(self):
        suggestions = _memory_suggestions(
            ["Milk", "Tomatoes", "Olive oil"],
            ["Tnuva", "Kitchenware", "Produce market"],
        )
        self.assertEqual(len(suggestions), 4)

    def test_advanced_filters_are_nested_in_primary_workspace_and_collapsed(self):
        tree = ast.parse(textwrap.dedent(inspect.getsource(render_database_archive)))
        workspace = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.With)
            and any(
                isinstance(item.context_expr, ast.Call)
                and isinstance(item.context_expr.func, ast.Name)
                and item.context_expr.func.id == "primary_workspace"
                and any(
                    keyword.arg == "key"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value == "search"
                    for keyword in item.context_expr.keywords
                )
                for item in node.items
            )
        )
        expander = next(
            node
            for node in ast.walk(workspace)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "expander"
        )

        self.assertEqual(expander.args[0].value, "Advanced filters")
        expanded = next(
            keyword.value
            for keyword in expander.keywords
            if keyword.arg == "expanded"
        )
        self.assertIs(expanded.value, False)

    def test_search_uses_streamlit_native_live_typeahead(self):
        source = inspect.getsource(render_database_archive)
        self.assertIn("search_field.selectbox(", source)
        self.assertIn("accept_new_options=True", source)
        self.assertIn('filter_mode="fuzzy"', source)
        self.assertIn("on_change=_apply_memory_search_input", source)
        self.assertIn('search_action.button(\n                "Search"', source)
        self.assertIn('st.expander(\n                "Advanced filters"', source)

    def test_live_option_keeps_memory_label_first(self):
        suggestion = SearchSuggestion(
            "Supplier",
            "אקר מחשבים",
            "Invoice #257940",
            1,
        )
        self.assertEqual(
            _format_memory_search_option(suggestion),
            "אקר מחשבים · Supplier",
        )

    def test_live_catalog_is_available_before_submit_and_selection_opens_invoice(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            environment = {
                "BARNI_DATA_ROOT": str(root),
                "OPENAI_API_KEY": "test-placeholder",
            }
            with patch.dict(os.environ, environment):
                init_database(root / "invoice_archive.db")
                source = root / "aker.pdf"
                source.write_bytes(b"invoice")
                insert_invoice(source, {
                    "document_type": "חשבונית מס",
                    "supplier": "אקר מחשבים",
                    "supplier_id": "aker-vat",
                    "invoice_number": "257940",
                    "invoice_date": "2026-08-10",
                    "total": 120,
                    "items": [{
                        "description": "מפצל לאל פסק",
                        "quantity": 1,
                        "unit": "unit",
                        "unit_price": 120,
                        "line_total": 120,
                    }],
                })
                BusinessIdentityRepository().sync_existing_memory()
                FirstFeedState().complete(invoice_id=1)

                app_path = Path(__file__).resolve().parents[1] / "app.py"
                app = AppTest.from_file(str(app_path), default_timeout=10)
                app.session_state["barni_entered"] = True
                app.session_state["current_page"] = "חיפוש חשבוניות"
                app.run()

                search = next(box for box in app.selectbox if box.label == "Search")
                self.assertIn("אקר מחשבים · Supplier", search.options)
                self.assertIn("מפצל לאל פסק · Product", search.options)

                app = search.select("אקר מחשבים · Supplier").run()

        self.assertFalse(app.exception)
        self.assertIn(
            "## אקר מחשבים",
            [item.value for item in app.markdown],
        )

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
