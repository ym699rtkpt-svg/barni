from __future__ import annotations

import unittest

from hybrid_engine import reconcile_extracted_financials, validate_document
from review_form import _field_needs_review


def _document(**overrides) -> dict:
    document = {
        "document_type": "חשבונית מס",
        "supplier": "Pilot Supplier",
        "supplier_id": "515000001",
        "invoice_number": "INV-1",
        "invoice_date": "2026-08-10",
        "subtotal": 445.76,
        "taxable_amount": 445.76,
        "exempt_amount": 0.0,
        "vat_rate": 0.0,
        "vat": 80.24,
        "total": 526.0,
        "tax_treatment": "חייב במע״מ",
        "currency": "ILS",
        "items": [{"description": "Olive oil", "line_total": 445.76}],
        "warnings": [],
        "confidence": 0.98,
    }
    document.update(overrides)
    return document


class FinancialConsistencyTests(unittest.TestCase):
    def test_zero_rate_is_reconciled_to_18_percent_from_exact_amounts(self):
        source = _document()
        reconciled = reconcile_extracted_financials(source)
        validation = validate_document(reconciled)

        self.assertEqual(reconciled["vat_rate"], 18.0)
        self.assertEqual(
            reconciled["vat_rate_source"],
            "derived_from_financial_evidence",
        )
        self.assertEqual(reconciled["taxable_amount"], 445.76)
        self.assertEqual(reconciled["vat"], 80.24)
        self.assertEqual(reconciled["total"], 526.0)
        self.assertNotIn("vat_rate_mismatch", validation["machine_issues"])
        self.assertNotIn("missing_vat_rate", validation["machine_issues"])

    def test_unknown_tax_treatment_still_reconciles_explicit_taxable_evidence(self):
        reconciled = reconcile_extracted_financials(_document(
            vat_rate=None,
            tax_treatment="לא ברור",
        ))

        self.assertEqual(reconciled["vat_rate"], 18.0)
        self.assertNotIn(
            "missing_vat_rate",
            validate_document(reconciled)["machine_issues"],
        )

    def test_valid_18_percent_values_remain_unchanged(self):
        source = _document(
            subtotal=1080.0,
            taxable_amount=1080.0,
            vat=194.4,
            total=1274.4,
            vat_rate=18.0,
        )

        reconciled = reconcile_extracted_financials(source)

        self.assertEqual(reconciled["vat_rate"], 18.0)
        self.assertNotIn("vat_rate_source", reconciled)
        self.assertEqual(validate_document(reconciled)["status"], "pass")

    def test_currency_rounding_tolerance_allows_safe_derivation(self):
        reconciled = reconcile_extracted_financials(_document(
            subtotal=445.77,
            taxable_amount=445.77,
            vat=80.24,
            total=526.01,
            vat_rate=None,
        ))

        self.assertEqual(reconciled["vat_rate"], 18.0)
        self.assertEqual(validate_document(reconciled)["status"], "pass")

    def test_ambiguous_rate_remains_needs_attention(self):
        unresolved = reconcile_extracted_financials(_document(
            vat=73.55,
            total=519.31,
            vat_rate=None,
        ))
        validation = validate_document(unresolved)

        self.assertIsNone(unresolved["vat_rate"])
        self.assertIn("missing_vat_rate", validation["machine_issues"])
        self.assertEqual(validation["status"], "review")
        self.assertTrue(
            _field_needs_review(set(validation["machine_issues"]), "vat_rate")
        )

    def test_foreign_currency_rate_is_not_derived_from_israeli_rate_policy(self):
        unresolved = reconcile_extracted_financials(_document(
            currency="EUR",
            vat_rate=None,
        ))

        self.assertIsNone(unresolved["vat_rate"])
        self.assertIn(
            "missing_vat_rate",
            validate_document(unresolved)["machine_issues"],
        )

    def test_exempt_invoice_remains_valid_without_vat_rate(self):
        exempt = _document(
            subtotal=100.0,
            taxable_amount=None,
            exempt_amount=100.0,
            vat_rate=None,
            vat=0.0,
            total=100.0,
            tax_treatment="פטור ממע״מ",
        )

        reconciled = reconcile_extracted_financials(exempt)
        validation = validate_document(reconciled)

        self.assertIsNone(reconciled["vat_rate"])
        self.assertEqual(validation["status"], "pass")

    def test_mixed_taxable_and_exempt_invoice_remains_valid(self):
        mixed = _document(
            subtotal=150.0,
            taxable_amount=100.0,
            exempt_amount=50.0,
            vat_rate=18.0,
            vat=18.0,
            total=168.0,
            tax_treatment="מעורב",
        )

        reconciled = reconcile_extracted_financials(mixed)
        validation = validate_document(reconciled)

        self.assertEqual(reconciled["vat_rate"], 18.0)
        self.assertEqual(validation["status"], "pass")

    def test_subtotal_contradiction_is_flagged(self):
        validation = validate_document(_document(
            subtotal=400.0,
            vat_rate=18.0,
        ))

        self.assertIn("subtotal_mismatch", validation["machine_issues"])
        self.assertTrue(
            _field_needs_review(set(validation["machine_issues"]), "subtotal")
        )


if __name__ == "__main__":
    unittest.main()
