from __future__ import annotations

import unittest

from services.business_facts import BusinessFact, ComparablePriceFact, FactStatus, PriceComparison
from services.business_identity import InvoiceEvidence
from services.business_stories import BusinessStory, StoryCategory, StoryEvidence
from services.evidence import (
    Claim, Confidence, ConfidenceStatus, ConfidenceType,
    ConfidenceTypeMismatchError, EvidenceContractError, EvidenceRef,
    LOCAL_BUSINESS_ID, SourceType, combine_confidence, invoice_ref,
    source_invoice_id,
)
from services.identity_review import IdentityReviewCandidate


def price_fact(invoice_id: int, line_id: int, price: float) -> ComparablePriceFact:
    evidence = {
        "invoice_ids": [invoice_id], "invoice_item_ids": [line_id],
        "observed_values": {"unit_price": price},
    }
    fact = BusinessFact(None, "comparable_price", f"price-{line_id}", "invoice_item",
                        line_id, FactStatus.TRUSTED, 1.0, "Comparable",
                        {"unit": 1.0}, evidence, {}, "2026-07-01")
    return ComparablePriceFact(fact, 1, "Milk", 2, "Tnuva", invoice_id, line_id,
                               price, price, "unit", 1, "unit", 1,
                               "EXCLUSIVE", "ILS", "2026-07-01", "invoice", False)


class EvidenceContractTests(unittest.TestCase):
    def test_price_claim_links_both_invoice_lines(self):
        previous, current = price_fact(10, 100, 7), price_fact(11, 110, 8)
        comparison = PriceComparison(current, previous, True, FactStatus.TRUSTED,
                                     "Comparable", 1, 14.28, (10, 11))
        self.assertEqual({source_invoice_id(ref) for ref in comparison.claim.evidence}, {10, 11})
        self.assertEqual({ref.subrecord_id for ref in comparison.claim.evidence}, {100, 110})

    def test_identity_review_exposes_typed_evidence(self):
        evidence = InvoiceEvidence(7, 7, "Tnuva", "841", "2026-07-31", 100,
                                   "invoice", "/invoice.pdf")
        candidate = IdentityReviewCandidate(1, "supplier", "supplier_match", 2, 3,
                                            "Tnuva", "Tnuva Ltd", "Possible match", "Because", .9,
                                            80, ("Same VAT ID",), (evidence,))
        self.assertEqual(candidate.evidence_refs[0].source_type, SourceType.INVOICE)
        self.assertEqual(source_invoice_id(candidate.evidence_refs[0]), 7)

    def test_story_preserves_structured_evidence(self):
        evidence = StoryEvidence(7, "Tnuva", "841", "2026-07-31", 100, "/invoice.pdf")
        story = BusinessStory("price_increase", "Price increased", "Milk increased.",
                              StoryCategory.PRICE, 90, evidence=(evidence,))
        self.assertEqual(story.claim.confidence.type, ConfidenceType.ANSWER)
        self.assertEqual(source_invoice_id(story.claim.evidence[0]), 7)

    def test_search_style_source_opening_uses_contract(self):
        self.assertEqual(source_invoice_id(invoice_ref(841)), 841)

    def test_business_scope_must_match(self):
        with self.assertRaises(EvidenceContractError):
            Claim("business-a", "test", "invoice", 1, "Claim",
                  (invoice_ref(1, business_id="business-b"),),
                  Confidence(ConfidenceType.OBSERVATION, ConfidenceStatus.SUPPORTED, 1),
                  "test", "1")

    def test_confidence_types_cannot_be_mixed(self):
        with self.assertRaises(ConfidenceTypeMismatchError):
            combine_confidence((
                Confidence(ConfidenceType.EXTRACTION, ConfidenceStatus.SUPPORTED, .9),
                Confidence(ConfidenceType.IDENTITY, ConfidenceStatus.SUPPORTED, .9),
            ))

    def test_supported_claim_requires_evidence(self):
        with self.assertRaises(EvidenceContractError):
            Claim(LOCAL_BUSINESS_ID, "test", "invoice", 1, "Unsupported",
                  (), Confidence(ConfidenceType.OBSERVATION, ConfidenceStatus.SUPPORTED, 1),
                  "test", "1")

    def test_legacy_price_evidence_remains_readable(self):
        fact = price_fact(10, 100, 7).fact
        self.assertEqual(fact.evidence_refs[0].source_id, 10)


if __name__ == "__main__":
    unittest.main()
