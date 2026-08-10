from __future__ import annotations

import ast
import json
import inspect
import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from services.product_state import FirstFeedState
from services.visible_learning import LearningSnapshot
from daily_intake import _render_feed_styles, _render_upload_controls
from ui.home import (
    _first_session_knowledge_summary,
    _monthly_activity,
    _order_home_priorities,
)


class FirstFeedOnboardingUITests(unittest.TestCase):
    @staticmethod
    def _markdown_values(app: AppTest) -> list[str]:
        return [item.value for item in app.markdown]

    @staticmethod
    def _sidebar_button(app: AppTest, label: str):
        return next(button for button in app.sidebar.button if button.label == label)

    def _open_product(self, root: Path) -> AppTest:
        environment = {
            "BARNI_DATA_ROOT": str(root),
            "OPENAI_API_KEY": "test-placeholder",
        }
        with patch.dict(os.environ, environment):
            app_path = Path(__file__).resolve().parents[1] / "app.py"
            app = AppTest.from_file(str(app_path), default_timeout=10).run()
            return app.button[0].click().run()

    def test_first_time_user_sees_single_invoice_introduction(self):
        with tempfile.TemporaryDirectory() as folder:
            app = self._open_product(Path(folder))

        self.assertFalse(app.exception)
        self.assertIn("## Hello. I'm Barni.", [item.value for item in app.markdown])
        self.assertEqual([uploader.label for uploader in app.file_uploader], ["Choose one invoice"])
        self.assertTrue(any(
            'data-testid="barni-first-feed-visual-cue"' in item.value
            for item in app.markdown
        ))

    def test_returning_user_enters_normal_product(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            FirstFeedState(root / "product-state.json").complete(invoice_id=1)
            app = self._open_product(root)

        self.assertFalse(app.exception)
        self.assertNotIn("## Hello. I'm Barni.", [item.value for item in app.markdown])
        self.assertFalse(any(
            'data-testid="barni-first-feed-visual-cue"' in item.value
            for item in app.markdown
        ))
        self.assertIn("## Welcome back", [item.value for item in app.markdown])
        self.assertIn("🏠  Home", [button.label for button in app.sidebar.button])

    def test_first_learning_confirmation_does_not_block_the_product(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            FirstFeedState(root / "product-state.json").complete(invoice_id=1)
            environment = {
                "BARNI_DATA_ROOT": str(root),
                "OPENAI_API_KEY": "test-placeholder",
            }
            with patch.dict(os.environ, environment):
                app_path = Path(__file__).resolve().parents[1] / "app.py"
                app = AppTest.from_file(str(app_path), default_timeout=10)
                app.session_state["barni_entered"] = True
                app.session_state["barni_first_feed_transition_pending"] = True
                app.session_state["daily_intake_completion"] = {
                    "outcome": "saved",
                    "invoices": 1,
                    "suppliers": 1,
                    "products": 3,
                    "price_points": 0,
                }
                app.run()
                values = self._markdown_values(app)
                self.assertFalse(app.exception)
                self.assertIn("### Barni learned", values)
                self.assertIn("+1 supplier", values)
                self.assertIn("+3 products", values)
                self.assertNotIn("+0 comparable prices", values)
                self.assertIn(
                    "## I know a little about your business now.",
                    values,
                )
                self.assertNotIn("## Welcome back", values)
                self.assertIn("🏠  Home", [button.label for button in app.sidebar.button])

                app = self._sidebar_button(app, "🔍  Search Invoices").click().run()
                values = self._markdown_values(app)
                self.assertNotIn("### Barni learned", values)
                self.assertNotIn("## Welcome back", values)
                self.assertNotIn("BARNI · YOUR BUSINESS ASSISTANT", values)

                app = self._sidebar_button(app, "📄  Feed Barni").click().run()
                values = self._markdown_values(app)
                self.assertNotIn("### Barni learned", values)
                self.assertNotIn("## Welcome back", values)
                self.assertNotIn("BARNI · YOUR BUSINESS ASSISTANT", values)

    def test_feed_has_one_upload_entry_and_no_redundant_sections(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            FirstFeedState(root / "product-state.json").complete(invoice_id=1)
            environment = {
                "BARNI_DATA_ROOT": str(root),
                "OPENAI_API_KEY": "test-placeholder",
            }
            with patch.dict(os.environ, environment):
                app_path = Path(__file__).resolve().parents[1] / "app.py"
                app = AppTest.from_file(str(app_path), default_timeout=10)
                app.session_state["barni_entered"] = True
                app.session_state["current_page"] = "קליטה יומית"
                app.run()

                values = self._markdown_values(app)
                self.assertFalse(app.exception)
                self.assertEqual(
                    [button.label for button in app.button].count("Feed Barni"),
                    1,
                )
                self.assertEqual(values.count("## Feed Barni"), 1)
                self.assertIn("### Ready for today's invoices", values)
                self.assertNotIn("### Feed today's invoices", values)
                self.assertNotIn(
                    "Every invoice makes Barni smarter.",
                    [item.value for item in app.caption],
                )
                self.assertEqual(len(app.file_uploader), 0)

                feed_button = next(
                    button for button in app.button if button.label == "Feed Barni"
                )
                app = feed_button.click().run()
                self.assertFalse(app.exception)
                self.assertEqual(
                    [uploader.label for uploader in app.file_uploader],
                    ["Drop invoices here"],
                )
                self.assertNotIn(
                    "Feed Barni",
                    [button.label for button in app.button],
                )

    def test_unfinished_feed_groups_primary_and_secondary_actions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            FirstFeedState(root / "product-state.json").complete(invoice_id=1)
            queue_path = root / "daily-intake" / "queue.json"
            queue_path.parent.mkdir(parents=True)
            queue_path.write_text(
                json.dumps([
                    {
                        "id": "review-1",
                        "created_at": "2026-08-10T09:00:00",
                        "queue_status": "review",
                        "document": {"machine_issues": ["missing_supplier"]},
                    }
                ]),
                encoding="utf-8",
            )
            environment = {
                "BARNI_DATA_ROOT": str(root),
                "OPENAI_API_KEY": "test-placeholder",
            }
            with patch.dict(os.environ, environment):
                app_path = Path(__file__).resolve().parents[1] / "app.py"
                app = AppTest.from_file(str(app_path), default_timeout=10)
                app.session_state["barni_entered"] = True
                app.session_state["current_page"] = "קליטה יומית"
                app.run()

                initial_values = self._markdown_values(app)
                initial_action_labels = [button.label for button in app.button]
                initial_uploader_count = len(app.file_uploader)

                feed_button = next(
                    button for button in app.button if button.label == "Feed Barni"
                )
                app_with_uploader = feed_button.click().run()

        self.assertFalse(app.exception)
        self.assertIn("### Finish what you started", initial_values)
        self.assertEqual(
            initial_action_labels[:2],
            ["Continue review", "Feed Barni"],
        )
        self.assertEqual(initial_uploader_count, 0)
        self.assertFalse(app_with_uploader.exception)
        self.assertEqual(len(app_with_uploader.file_uploader), 1)
        self.assertIn(
            "Continue review",
            [button.label for button in app_with_uploader.button],
        )
        self.assertNotIn(
            "Feed Barni",
            [button.label for button in app_with_uploader.button],
        )

    def test_selecting_first_invoice_removes_idle_cue_without_starting_workflow(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            environment = {
                "BARNI_DATA_ROOT": str(root),
                "OPENAI_API_KEY": "test-placeholder",
            }
            with patch.dict(os.environ, environment):
                app_path = Path(__file__).resolve().parents[1] / "app.py"
                app = AppTest.from_file(str(app_path), default_timeout=10).run()
                app = app.button[0].click().run()
                self.assertTrue(any(
                    'data-testid="barni-first-feed-visual-cue"' in item.value
                    for item in app.markdown
                ))

                app = app.file_uploader[0].upload(
                    "first-invoice.pdf",
                    b"%PDF-1.4\n%%EOF",
                    "application/pdf",
                ).run()

                self.assertFalse(app.exception)
                self.assertFalse(any(
                    'data-testid="barni-first-feed-visual-cue"' in item.value
                    for item in app.markdown
                ))
                self.assertIn("Read invoice", [button.label for button in app.button])
                self.assertNotIn(
                    "daily_intake_flow",
                    app.session_state.filtered_state,
                )
                self.assertFalse(FirstFeedState(root / "product-state.json").is_complete())

    def test_first_feed_cue_has_reduced_motion_static_fallback(self):
        styles = inspect.getsource(_render_feed_styles)
        self.assertIn("@media (prefers-reduced-motion: reduce)", styles)
        self.assertIn(".barni-first-feed-cue-document", styles)
        self.assertIn("animation: none", styles)

    def test_first_feed_cue_is_rendered_inside_upload_workspace(self):
        tree = ast.parse(textwrap.dedent(inspect.getsource(_render_upload_controls)))
        upload_workspace = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.With)
            and any(
                isinstance(item.context_expr, ast.Call)
                and isinstance(item.context_expr.func, ast.Attribute)
                and item.context_expr.func.attr == "container"
                and any(
                    keyword.arg == "key"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value == "feed_upload"
                    for keyword in item.context_expr.keywords
                )
                for item in node.items
            )
        )
        self.assertTrue(any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_render_first_feed_visual_cue"
            for node in ast.walk(upload_workspace)
        ))

    def test_first_session_summary_uses_canonical_memory_counts(self):
        summary = _first_session_knowledge_summary(LearningSnapshot(
            invoices=1,
            suppliers=1,
            products=1,
        ))
        self.assertEqual(
            summary,
            "I now remember 1 supplier, 1 product, and 1 approved invoice.",
        )

    def test_monthly_activity_keeps_prior_knowledge_out_of_calendar_metrics(self):
        invoices = pd.DataFrame([
            {
                "id": 1,
                "invoice_date": "2026-07-31",
                "supplier": "Earlier Supplier",
                "total": 566.40,
            },
            {
                "id": 2,
                "invoice_date": "2026-08-02",
                "supplier": "Current Supplier",
                "total": 100.00,
            },
        ])

        _, count, spend, suppliers = _monthly_activity(
            invoices,
            current_month=pd.Period("2026-08", freq="M"),
        )

        self.assertEqual(count, 1)
        self.assertEqual(spend, 100.00)
        self.assertEqual(suppliers, 1)

    def test_first_session_labels_monthly_activity_separately_from_memory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            FirstFeedState(root / "product-state.json").complete(invoice_id=1)
            environment = {
                "BARNI_DATA_ROOT": str(root),
                "OPENAI_API_KEY": "test-placeholder",
            }
            with patch.dict(os.environ, environment):
                app_path = Path(__file__).resolve().parents[1] / "app.py"
                app = AppTest.from_file(str(app_path), default_timeout=10)
                app.session_state["barni_entered"] = True
                app.session_state["barni_first_feed_transition_pending"] = True
                app.run()

        self.assertFalse(app.exception)
        self.assertIn(
            "Current calendar month only — separate from the total knowledge "
            "Barni remembers above.",
            [caption.value for caption in app.caption],
        )
        self.assertIn(
            "Products Barni knows (all time)",
            [metric.label for metric in app.metric],
        )

    def test_identity_review_stays_supporting_during_first_session(self):
        normal = SimpleNamespace(story_type="invoice_approved")
        identity = SimpleNamespace(story_type="identity_review_needed")
        price = SimpleNamespace(story_type="price_change")
        ordered = _order_home_priorities(
            [identity, normal, price],
            first_session=True,
        )
        self.assertEqual(ordered, [normal, price, identity])
        self.assertIn(identity, ordered)

    def test_search_and_feed_do_not_render_home_hero(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            FirstFeedState(root / "product-state.json").complete(invoice_id=1)
            environment = {
                "BARNI_DATA_ROOT": str(root),
                "OPENAI_API_KEY": "test-placeholder",
            }
            with patch.dict(os.environ, environment):
                app_path = Path(__file__).resolve().parents[1] / "app.py"
                for page in ("חיפוש חשבוניות", "קליטה יומית"):
                    app = AppTest.from_file(str(app_path), default_timeout=10)
                    app.session_state["barni_entered"] = True
                    app.session_state["current_page"] = page
                    app.run()
                    values = self._markdown_values(app)
                    self.assertFalse(app.exception)
                    self.assertNotIn("## Welcome back", values)
                    self.assertNotIn("BARNI · YOUR BUSINESS ASSISTANT", values)
                    if page == "חיפוש חשבוניות":
                        self.assertIn(
                            "Advanced filters",
                            [status.label for status in app.status],
                        )
                        self.assertEqual(
                            {widget.label for widget in app.multiselect},
                            {"Tags", "Document type", "Status"},
                        )


if __name__ == "__main__":
    unittest.main()
