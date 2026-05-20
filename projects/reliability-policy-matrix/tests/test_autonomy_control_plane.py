from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from autonomy_control_plane import _validate_capabilities, _validate_policy


class AutonomyControlPlaneTest(unittest.TestCase):
    def test_forbidden_capability_is_rejected(self) -> None:
        errors = _validate_capabilities(
            {
                "forbidden_capabilities": ["raw_docker_control"],
                "capabilities": [
                    {
                        "name": "raw_docker_control",
                        "risk": "production_write",
                        "enabled": True,
                        "rollback": "none",
                    }
                ],
            }
        )

        self.assertTrue(any("forbidden capabilities" in error for error in errors))

    def test_policy_requires_human_approval_for_secret_bearing(self) -> None:
        errors = _validate_policy(
            {
                "policy": {
                    "read_only": "allow",
                    "comment_only": "allow_scoped",
                    "low_risk_write": "pr_or_canary_only",
                    "production_write": "canary_rollback_alert_required",
                    "destructive": "human_approval_required",
                    "secret_bearing": "human_approval_required",
                }
            }
        )

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
