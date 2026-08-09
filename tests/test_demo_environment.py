from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from demo_environment import DEMO_BUSINESS_NAME, seed_demo, verify_demo


class DemoEnvironmentTests(unittest.TestCase):
    def test_seeded_demo_exercises_the_customer_data_contracts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "demo-data"

            manifest = seed_demo(root, today=date(2026, 8, 9))
            verification = verify_demo(root)

        self.assertEqual(manifest["business_name"], DEMO_BUSINESS_NAME)
        self.assertEqual(manifest["accounting_month"], "2026-08")
        self.assertTrue(all(verification["checks"].values()))

    def test_seed_refuses_to_overwrite_existing_demo_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "demo-data"
            seed_demo(root, today=date(2026, 8, 9))

            with self.assertRaisesRegex(RuntimeError, "Reset it first"):
                seed_demo(root, today=date(2026, 8, 9))


if __name__ == "__main__":
    unittest.main()
