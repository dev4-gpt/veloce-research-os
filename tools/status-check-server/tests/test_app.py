from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app


class StatusCheckTest(unittest.TestCase):
    def test_rejects_unknown_target(self) -> None:
        status, payload = app.run_status_check({"target": "example.com"})
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])
        self.assertIn("invalid target", payload["detail"])

    def test_clamps_timeout(self) -> None:
        self.assertEqual(app.clamp_timeout_ms(1), 500)
        self.assertEqual(app.clamp_timeout_ms(99999), 5000)
        self.assertEqual(app.clamp_timeout_ms(1500), 1500)

    def test_openapi_has_status_check(self) -> None:
        self.assertIn("/status_check", app.OPENAPI_SPEC["paths"])
        operation = app.OPENAPI_SPEC["paths"]["/status_check"]["post"]
        self.assertEqual(operation["operationId"], "status_check")


if __name__ == "__main__":
    unittest.main()
