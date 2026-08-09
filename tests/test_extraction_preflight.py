from __future__ import annotations

import unittest

from ai_extractor import extraction_service_ready


class ExtractionPreflightTests(unittest.TestCase):
    def test_ready_when_credential_is_present(self):
        self.assertTrue(extraction_service_ready({"OPENAI_API_KEY": "configured"}))

    def test_not_configured_when_credential_is_missing(self):
        self.assertFalse(extraction_service_ready({}))

    def test_not_configured_when_credential_is_blank(self):
        self.assertFalse(extraction_service_ready({"OPENAI_API_KEY": "   "}))


if __name__ == "__main__":
    unittest.main()
