from __future__ import annotations

import unittest

from services.barni_thinking import think_about_invoice


class BarniThinkingTests(unittest.TestCase):
    def test_known_supplier_uses_real_history_count(self):
        invoice = {
            "id": 3,
            "supplier": "Tnuva",
            "supplier_id": "1",
            "document_type": "Invoice",
            "invoice_number": "3",
            "invoice_date": "2026-08-01",
            "total": 100,
            "confidence": 0.95,
        }
        history = [
            {"id": 1, "supplier": "Tnuva", "supplier_id": "1"},
            {"id": 2, "supplier": "Tnuva", "supplier_id": "1"},
            invoice,
        ]

        thinking = think_about_invoice(invoice, [], history)

        memory = next(section for section in thinking.sections if section.name == "Memory")
        self.assertEqual(memory.statements, ("I found 2 earlier invoices from Tnuva.",))

    def test_missing_fields_are_explained_without_technical_language(self):
        invoice = {"document_type": "Invoice", "confidence": 0.43}

        thinking = think_about_invoice(invoice, [], [])
        rendered_text = " ".join(
            statement
            for section in thinking.sections
            for statement in section.statements
        ).lower()

        self.assertIn("couldn't confidently identify the supplier", rendered_text)
        self.assertIn("i need your help", rendered_text)
        self.assertNotIn("ocr", rendered_text)
        self.assertNotIn("parser", rendered_text)
        self.assertNotIn("0.43", rendered_text)

    def test_possible_duplicate_becomes_the_recommendation(self):
        invoice = {
            "id": 2,
            "supplier": "Tnuva",
            "supplier_id": "1",
            "document_type": "Invoice",
            "invoice_number": "841",
            "invoice_date": "2026-08-01",
            "total": 100,
        }
        history = [
            {
                "id": 1,
                "supplier": "Tnuva",
                "supplier_id": "1",
                "document_type": "Invoice",
                "invoice_number": "841",
                "invoice_date": "2026-07-01",
            }
        ]

        thinking = think_about_invoice(invoice, [], history)

        recommendation = next(
            section for section in thinking.sections if section.name == "Recommendation"
        )
        self.assertIn("Compare the invoices", recommendation.statements[0])

    def test_approved_invoice_is_not_recommended_for_approval_again(self):
        invoice = {
            "id": 1,
            "status": "approved",
            "supplier": "Tnuva",
            "document_type": "Invoice",
            "invoice_number": "841",
            "invoice_date": "2026-08-01",
            "total": 100,
            "confidence": 0.95,
        }

        thinking = think_about_invoice(invoice, [], [invoice])
        recommendation = next(
            section for section in thinking.sections if section.name == "Recommendation"
        )

        self.assertIn("remembered this approved invoice", recommendation.statements[0])
        self.assertNotIn("already in Business Memory", recommendation.statements[0])
        self.assertNotIn("approve it", recommendation.statements[0])

    def test_first_approved_invoice_is_distinguished_from_earlier_history(self):
        invoice = {
            "id": 1,
            "status": "approved",
            "supplier": "ראש חץ",
            "document_type": "חשבונית מס",
            "invoice_number": "50544",
            "invoice_date": "2026-06-24",
            "total": 566.40,
            "confidence": 0.95,
        }

        thinking = think_about_invoice(invoice, [], [invoice])
        identity = next(
            section for section in thinking.sections if section.name == "Identity"
        )
        memory = next(
            section for section in thinking.sections if section.name == "Memory"
        )
        rendered = " ".join(
            statement
            for section in thinking.sections
            for statement in section.statements
        )

        self.assertEqual(
            identity.statements,
            (
                "I recognize the document type as חשבונית מס, and it belongs to "
                "ראש חץ.",
            ),
        )
        self.assertEqual(
            memory.statements,
            ("This is the first approved invoice I know from ראש חץ.",),
        )
        self.assertNotIn("already in Business Memory", rendered)
        self.assertNotIn("haven't seen a previous invoice", rendered)


if __name__ == "__main__":
    unittest.main()
