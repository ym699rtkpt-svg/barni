from __future__ import annotations

import unittest

from services.invoice_intelligence import (
    Category,
    Insight,
    InvoiceIntelligenceContext,
    InvoiceIntelligenceEngine,
    NearDuplicateInvoiceRule,
    PriceMovementRule,
    ProductKnowledgeRule,
    RecurringPurchaseRule,
    RepeatedPriceIncreaseRule,
    Severity,
    SupplierProductNoveltyRule,
    UnusualInvoiceTotalRule,
    analyze_invoice,
    select_proactive_insights,
)


def invoice(invoice_id: int, **overrides):
    record = {
        "id": invoice_id,
        "supplier": "Tnuva",
        "supplier_id": "vat-1",
        "invoice_number": str(invoice_id),
        "document_type": "Invoice",
        "invoice_date": f"2026-01-{invoice_id:02d}",
        "total": 100.0,
    }
    record.update(overrides)
    return record


def trusted_price(price: float, unit: str = "l", **values):
    record = {
        "unit_price": price,
        "normalized_price": price,
        "normalized_unit": unit,
        "package_quantity": 1.0,
        "package_unit": unit,
        "fact_status": "TRUSTED",
    }
    record.update(values)
    return record


class InvoiceIntelligenceTests(unittest.TestCase):
    def test_missing_number_and_first_supplier_are_structured(self):
        current = invoice(1, invoice_number="")
        insights = analyze_invoice(InvoiceIntelligenceContext(invoice=current, invoices=[current]))

        self.assertEqual(insights[0].title, "Missing Invoice Number")
        self.assertEqual(insights[0].severity, Severity.ATTENTION)
        self.assertEqual(insights[0].category, Category.COMPLETENESS)
        self.assertEqual(insights[0].confidence, 1.0)
        self.assertIn("First Supplier Invoice", [insight.title for insight in insights])

    def test_draft_source_identifier_is_preserved_as_evidence(self):
        current = invoice(0, source_record_id="queue-123")

        insights = analyze_invoice(InvoiceIntelligenceContext(invoice=current, invoices=[]))
        first_supplier = next(
            insight for insight in insights if insight.title == "First Supplier Invoice"
        )

        self.assertEqual(first_supplier.source_record_ids, ("queue-123",))

    def test_existing_supplier_does_not_add_noise_to_duplicate(self):
        previous = invoice(1, invoice_number="22")
        current = invoice(2, invoice_number="22")
        insights = analyze_invoice(
            InvoiceIntelligenceContext(invoice=current, invoices=[previous, current])
        )
        titles = [insight.title for insight in insights]

        self.assertEqual(titles[0], "Possible Duplicate")
        self.assertNotIn("Known Supplier", titles)
        self.assertNotIn("First Supplier Invoice", titles)

    def test_near_duplicate_requires_same_date_total_and_reordered_number_parts(self):
        previous = invoice(1, invoice_number="26/3802", total=3378.0)
        current = invoice(2, invoice_number="3802/26", total=3378.0)
        previous["invoice_date"] = current["invoice_date"]
        engine = InvoiceIntelligenceEngine(rules=[NearDuplicateInvoiceRule()])

        insights = engine.analyze(
            InvoiceIntelligenceContext(invoice=current, invoices=[previous, current])
        )

        self.assertEqual(insights[0].title, "Possible Similar Invoice")
        self.assertEqual(insights[0].source_record_ids, (1, 2))
        self.assertEqual(insights[0].evidence["matching_invoice_numbers"], ["26/3802"])

        first_supplier = Insight(
            title="First Supplier Invoice",
            description="First",
            severity=Severity.POSITIVE,
            category=Category.SUPPLIER,
            confidence=1.0,
            priority=70,
            proactive=True,
        )
        self.assertEqual(
            [item.title for item in select_proactive_insights([*insights, first_supplier])],
            ["Possible Similar Invoice"],
        )

    def test_unusual_total_requires_three_previous_totals(self):
        history = [invoice(index, total=100.0) for index in range(1, 4)]
        current = invoice(4, total=500.0)
        insights = analyze_invoice(
            InvoiceIntelligenceContext(invoice=current, invoices=[*history, current])
        )

        unusual = next(insight for insight in insights if insight.title == "Unusual Invoice Total")
        self.assertEqual(unusual.category, Category.SPEND)
        self.assertEqual(unusual.evidence["typical_total"], 100.0)
        self.assertEqual(unusual.source_record_ids, (1, 2, 3, 4))
        self.assertTrue(unusual.recommended_next_action)
        self.assertEqual(unusual.explanation, unusual.description)

    def test_credit_note_total_does_not_create_impossible_percentage(self):
        history = [invoice(index, total=100.0) for index in range(1, 4)]
        current = invoice(4, total=-200.0)
        engine = InvoiceIntelligenceEngine(rules=[UnusualInvoiceTotalRule()])

        insights = engine.analyze(
            InvoiceIntelligenceContext(invoice=current, invoices=[*history, current])
        )

        self.assertEqual(insights, [])

    def test_price_increase_and_decrease_use_comparable_history(self):
        current = invoice(3)
        histories = {
            "Milk": [
                trusted_price(10.0, invoice_id=1, invoice_date="2026-01-01", supplier="Tnuva"),
                trusted_price(12.0, invoice_id=3, invoice_date="2026-01-03", supplier="Tnuva"),
            ],
            "Cream": [
                trusted_price(20.0, invoice_id=1, invoice_date="2026-01-01", supplier="Tnuva"),
                trusted_price(16.0, invoice_id=3, invoice_date="2026-01-03", supplier="Tnuva"),
            ],
        }
        items = [
            trusted_price(12.0, description="Milk", quantity=1, line_type="product"),
            trusted_price(16.0, description="Cream", quantity=1, line_type="product"),
        ]
        engine = InvoiceIntelligenceEngine(rules=[PriceMovementRule()], max_insights=3)
        insights = engine.analyze(InvoiceIntelligenceContext(
            invoice=current,
            items=items,
            price_histories=histories,
        ))

        self.assertEqual({insight.title for insight in insights}, {"Price Increase", "Price Decrease"})
        self.assertTrue(all(insight.confidence == 0.98 for insight in insights))
        increase = next(insight for insight in insights if insight.title == "Price Increase")
        self.assertTrue(increase.proactive)
        self.assertEqual(increase.source_record_ids, (1, 3))

    def test_new_product_uses_business_wide_history(self):
        current = invoice(2)
        item = {"description": "Olive Oil", "quantity": 1, "unit": "L", "unit_price": 48.0, "line_type": "product"}
        history = [{"invoice_id": 2, "invoice_date": "2026-01-02", "supplier": "Tnuva", "unit": "L", "unit_price": 48.0}]
        engine = InvoiceIntelligenceEngine(rules=[ProductKnowledgeRule()])
        insights = engine.analyze(InvoiceIntelligenceContext(
            invoice=current,
            items=[item],
            price_histories={"Olive Oil": history},
        ))

        self.assertEqual(insights[0].title, "New Product")
        self.assertEqual(insights[0].category, Category.PRODUCT)

    def test_vat_warning_requires_external_validation(self):
        current = invoice(1)
        without_validation = analyze_invoice(
            InvoiceIntelligenceContext(invoice=current, invoices=[current])
        )
        with_validation = analyze_invoice(InvoiceIntelligenceContext(
            invoice=current,
            invoices=[current],
            validations={"vat_warning": "VAT does not match the approved validation."},
        ))

        self.assertNotIn("VAT Needs Attention", [item.title for item in without_validation])
        self.assertIn("VAT Needs Attention", [item.title for item in with_validation])

    def test_new_rules_can_be_injected_without_changing_the_engine(self):
        class CustomRule:
            def evaluate(self, context):
                yield Insight(
                    title="Custom Insight",
                    description="A future rule can provide this.",
                    severity=Severity.INFO,
                    category=Category.LEARNING,
                    confidence=0.8,
                    priority=10,
                )

        engine = InvoiceIntelligenceEngine(rules=[CustomRule()])
        insights = engine.analyze(InvoiceIntelligenceContext(invoice=invoice(1)))

        self.assertEqual([insight.title for insight in insights], ["Custom Insight"])

    def test_repeated_price_increase_requires_three_rising_purchases(self):
        current = invoice(3)
        item = trusted_price(48.0, description="Olive Oil", quantity=2)
        history = [
            trusted_price(40.0, invoice_id=1, invoice_date="2026-01-01", supplier="Tnuva"),
            trusted_price(44.0, invoice_id=2, invoice_date="2026-01-02", supplier="Tnuva"),
        ]
        engine = InvoiceIntelligenceEngine(rules=[RepeatedPriceIncreaseRule()])

        insights = engine.analyze(InvoiceIntelligenceContext(
            invoice=current,
            items=[item],
            price_histories={"Olive Oil": history},
        ))

        self.assertEqual(insights[0].title, "Repeated Price Increase")
        self.assertEqual(insights[0].source_record_ids, (1, 2, 3))
        self.assertEqual(insights[0].evidence["prices"], [40.0, 44.0, 48.0])

    def test_repeated_increase_suppresses_redundant_single_step_signal(self):
        repeated = Insight(
            title="Repeated Price Increase",
            description="Repeated",
            severity=Severity.ATTENTION,
            category=Category.PRICE,
            confidence=0.99,
            priority=92,
            evidence={"product": "Olive Oil"},
            proactive=True,
        )
        latest = Insight(
            title="Price Increase",
            description="Latest",
            severity=Severity.ATTENTION,
            category=Category.PRICE,
            confidence=0.98,
            priority=88,
            evidence={"product": "Olive Oil"},
            proactive=True,
        )

        selected = select_proactive_insights([latest, repeated])

        self.assertEqual([insight.title for insight in selected], ["Repeated Price Increase"])

    def test_new_product_from_known_supplier_requires_global_product_history(self):
        previous_supplier = invoice(1)
        current = invoice(3)
        item = {"description": "Olive Oil", "unit_price": 48.0, "line_type": "product"}
        other_supplier_history = [
            {"invoice_id": 2, "invoice_date": "2026-01-02", "supplier": "Other", "unit_price": 42.0}
        ]
        engine = InvoiceIntelligenceEngine(rules=[SupplierProductNoveltyRule()])

        insights = engine.analyze(InvoiceIntelligenceContext(
            invoice=current,
            invoices=[previous_supplier, current],
            items=[item],
            price_histories={"Olive Oil": other_supplier_history},
        ))

        self.assertEqual(insights[0].title, "New Product From This Supplier")
        self.assertEqual(insights[0].evidence["previous_supplier_invoice_count"], 1)

    def test_supplier_alias_with_same_identity_does_not_create_false_new_product(self):
        previous_supplier = invoice(1, supplier="Supplier Alias A")
        current = invoice(2, supplier="Supplier Alias B")
        item = {"description": "Olive Oil", "unit_price": 48.0, "line_type": "product"}
        history = [
            {"invoice_id": 1, "invoice_date": "2026-01-01", "supplier": "Supplier Alias A", "unit_price": 42.0}
        ]
        engine = InvoiceIntelligenceEngine(rules=[SupplierProductNoveltyRule()])

        insights = engine.analyze(InvoiceIntelligenceContext(
            invoice=current,
            invoices=[previous_supplier, current],
            items=[item],
            price_histories={"Olive Oil": history},
        ))

        self.assertEqual(insights, [])

    def test_recurring_purchase_requires_five_consistent_dates(self):
        current = invoice(5, invoice_date="2026-01-29")
        item = {"description": "Milk", "line_type": "product"}
        history = [
            {"invoice_id": index, "invoice_date": date, "supplier": "Tnuva"}
            for index, date in enumerate(
                ["2026-01-01", "2026-01-08", "2026-01-15", "2026-01-22"],
                start=1,
            )
        ]
        engine = InvoiceIntelligenceEngine(rules=[RecurringPurchaseRule()])

        insights = engine.analyze(InvoiceIntelligenceContext(
            invoice=current,
            items=[item],
            price_histories={"Milk": history},
        ))

        self.assertEqual(insights[0].title, "Recurring Purchase Pattern")
        self.assertEqual(insights[0].evidence["intervals_days"], [7, 7, 7, 7])
        self.assertEqual(insights[0].source_record_ids, (1, 2, 3, 4, 5))

    def test_proactive_selector_stays_quiet_for_weak_price_change(self):
        current = invoice(2)
        item = trusted_price(10.6, description="Milk", quantity=1)
        history = [
            trusted_price(10.0, invoice_id=1, invoice_date="2026-01-01", supplier="Tnuva")
        ]
        engine = InvoiceIntelligenceEngine(rules=[PriceMovementRule()])
        insights = engine.analyze(InvoiceIntelligenceContext(
            invoice=current,
            items=[item],
            price_histories={"Milk": history},
        ))

        self.assertEqual(len(insights), 1)
        self.assertEqual(select_proactive_insights(insights), [])


if __name__ == "__main__":
    unittest.main()
