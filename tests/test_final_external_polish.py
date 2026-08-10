from __future__ import annotations

import inspect
import unittest

import daily_intake
import review_form
import smart_archive
import ui.business_memory
from ui.barni_thinking import render_barni_thinking


class FinalExternalPolishTests(unittest.TestCase):
    def test_wait_copy_is_truthful_short_and_provider_neutral(self):
        self.assertEqual(
            daily_intake.EXTRACTION_WAIT_MESSAGES,
            (
                "Reading invoice",
                "Understanding supplier and invoice details",
                "Understanding items and charges",
                "Preparing review",
            ),
        )
        copy = " ".join(daily_intake.EXTRACTION_WAIT_MESSAGES).lower()
        for technical_term in ("openai", "api", "provider", "ocr", "model"):
            self.assertNotIn(technical_term, copy)

    def test_wait_sequence_adds_no_blocking_or_artificial_delay(self):
        processing = inspect.getsource(daily_intake._render_processing_step)
        activity = inspect.getsource(daily_intake._render_extraction_activity)

        self.assertLess(
            processing.index("_render_extraction_activity()"),
            processing.index("process_files("),
        )
        self.assertNotIn("sleep(", processing)
        self.assertNotIn("sleep(", activity)
        self.assertIn("process_files(", processing)

    def test_review_keeps_primary_sections_and_approval_before_technical_details(self):
        review = inspect.getsource(daily_intake._render_review_step)
        form = inspect.getsource(review_form.document_review_form)

        for required in (
            "render_barni_thinking(",
            "_render_preview(record)",
            "document_review_form(",
            '"Approve & Teach Barni"',
            '"Skip for now"',
            '"More actions"',
        ):
            self.assertIn(required, review)
        self.assertIn('"Save changes"', form)
        self.assertLess(
            review.index('"Approve & Teach Barni"'),
            review.index('"Technical confidence details"'),
        )
        self.assertIn(
            'st.expander("Technical confidence details", expanded=False)',
            review,
        )

    def test_review_uses_compact_shared_narrative_density(self):
        review = inspect.getsource(daily_intake._render_review_step)
        narrative = inspect.getsource(render_barni_thinking)

        self.assertIn("compact=True", review)
        self.assertIn('density = "compact" if compact else "shell"', narrative)

    def test_mixed_invoice_lines_use_semantically_safe_review_language(self):
        form = inspect.getsource(review_form.document_review_form)

        self.assertIn('_review_label("Items & charges", issues, "items")', form)
        self.assertNotIn('_review_label("Products", issues, "items")', form)
        self.assertIn('document.get("items", [])', form)
        self.assertIn("st.data_editor(", form)
        self.assertNotIn("is_product_line", form)

    def test_canonical_product_surfaces_and_live_search_remain_present(self):
        memory = inspect.getsource(ui.business_memory.render_business_memory)
        search = inspect.getsource(smart_archive.render_database_archive)

        self.assertIn('"Products known"', memory)
        self.assertIn("search_suggestion_catalog", search)
        self.assertIn("accept_new_options=True", search)
        self.assertIn("search_action.button(", search)
        self.assertIn('"Search"', search)


if __name__ == "__main__":
    unittest.main()
