from __future__ import annotations

import unittest

from services.barni_thinking import BarniThinking, ThinkingSection
from ui.barni_thinking import _narrative_conclusion


class NarrativeReviewTests(unittest.TestCase):
    def _thinking(self, observation_tone="neutral", identity_tone="positive"):
        return BarniThinking(
            summary="I found a few details worth checking.",
            sections=(
                ThinkingSection("Identity", "", ("This is an invoice from Tnuva.",), identity_tone),
                ThinkingSection("Memory", "", ("I found two previous invoices.",)),
                ThinkingSection("Observations", "", ("Olive oil increased 14%.",), observation_tone),
                ThinkingSection("Confidence", "", ("The key details look consistent.",), "positive"),
                ThinkingSection("Recommendation", "", ("Review the latest price.",), "attention"),
            ),
        )

    def test_meaningful_observation_leads_the_narrative(self):
        conclusion, tone = _narrative_conclusion(self._thinking("attention"))
        self.assertEqual(conclusion, "Olive oil increased 14%.")
        self.assertEqual(tone, "attention")

    def test_identity_uncertainty_leads_when_observation_is_quiet(self):
        conclusion, tone = _narrative_conclusion(
            self._thinking("neutral", "attention")
        )
        self.assertEqual(conclusion, "This is an invoice from Tnuva.")
        self.assertEqual(tone, "attention")

    def test_supported_quiet_observation_is_the_default_conclusion(self):
        conclusion, tone = _narrative_conclusion(self._thinking())
        self.assertEqual(conclusion, "Olive oil increased 14%.")
        self.assertEqual(tone, "neutral")


if __name__ == "__main__":
    unittest.main()
