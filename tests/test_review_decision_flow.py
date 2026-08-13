from __future__ import annotations

import inspect
import unittest

import daily_intake
import review_form
import ui.business_memory
import ui.identity_review


class ReviewDecisionFlowTests(unittest.TestCase):
    def test_safe_invoice_has_no_attention_fields(self):
        record = {
            "queue_status": "ready",
            "document": {
                "confidence": 0.98,
                "machine_issues": [],
                "model_notes": [],
            },
        }

        self.assertEqual(review_form.review_attention_fields(record), ())
        state = inspect.getsource(daily_intake._render_review_state)
        self.assertIn('"## Everything looks good"', state)

    def test_issue_count_is_field_based_and_actionable(self):
        record = {
            "queue_status": "review",
            "document": {
                "confidence": 0.75,
                "machine_issues": ["missing_supplier", "missing_invoice_date"],
                "model_notes": [],
            },
        }

        attention = review_form.review_attention_fields(record)
        self.assertEqual(
            [(item.label, item.status) for item in attention],
            [("Supplier", "Missing"), ("Invoice date", "Missing")],
        )
        state = inspect.getsource(daily_intake._render_review_state)
        self.assertIn("I found {count}", state)

    def test_attention_and_fields_precede_collapsed_reasoning_and_actions_are_clear(self):
        review = inspect.getsource(daily_intake._render_review_step)
        form = inspect.getsource(review_form.document_review_form)

        self.assertLess(
            review.index("_render_review_state(record)"),
            review.index("document_review_form("),
        )
        self.assertLess(
            review.index("document_review_form("),
            review.index('st.expander("Why Barni thinks this", expanded=False)'),
        )
        self.assertLess(
            review.index('"Approve invoice"'),
            review.index('st.expander("Why Barni thinks this", expanded=False)'),
        )
        self.assertIn('"Save changes"', form)
        self.assertIn('"Skip for now"', review)
        self.assertIn('"Reject invoice"', review)
        self.assertIn("_render_preview(record)", review)

    def test_approval_finishes_without_identity_teaching_navigation(self):
        completion = inspect.getsource(daily_intake._render_approval_complete)
        approval = inspect.getsource(daily_intake._approve_record)
        return_home = inspect.getsource(daily_intake._return_home_after_approval)

        self.assertIn('"## Barni learned this invoice."', completion)
        self.assertIn('"Return to Home"', completion)
        self.assertIn('"Continue to next invoice"', completion)
        self.assertNotIn("Help Barni learn", completion)
        self.assertNotIn('current_page = "Identity Review"', approval)
        self.assertIn('candidate.story_type != "identity_review_needed"', approval)
        self.assertIn('current_page = "Barni"', return_home)

    def test_teaching_and_advanced_tools_remain_optional_in_business_memory(self):
        memory = inspect.getsource(ui.business_memory._render_identity_trust)
        corrections = inspect.getsource(ui.identity_review._manual_corrections)

        self.assertIn('"Help Barni learn"', memory)
        for action in ("Merge", "Split", "Rename"):
            self.assertIn(f'"{action}"', corrections)


if __name__ == "__main__":
    unittest.main()
