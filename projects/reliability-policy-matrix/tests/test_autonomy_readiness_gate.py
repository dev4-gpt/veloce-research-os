from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from autonomy_readiness_gate import _summarize


class AutonomyReadinessGateTest(unittest.TestCase):
    def test_blocked_critical_gate_blocks_readiness(self) -> None:
        report = _summarize(
            {
                "target_state": "unattended_autonomous_production",
                "gates": [
                    {
                        "id": "secret_rotation",
                        "severity": "critical",
                        "status": "blocked",
                        "owner": "VPS operator",
                        "action": "Rotate exposed secrets.",
                        "evidence_required": "stack-health passes after rotation.",
                    }
                ],
            },
            Path("configs/autonomy_readiness_v1_8.json"),
        )

        self.assertFalse(report["ok"])
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["critical_failures"], 1)
        self.assertEqual(report["next_actions"][0]["id"], "secret_rotation")

    def test_all_pass_gates_are_ready(self) -> None:
        report = _summarize(
            {
                "target_state": "unattended_autonomous_production",
                "gates": [
                    {
                        "id": "ruflo_boundary",
                        "severity": "critical",
                        "status": "pass",
                    }
                ],
            },
            Path("configs/autonomy_readiness_v1_8.json"),
        )

        self.assertTrue(report["ok"])
        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["critical_failures"], 0)


if __name__ == "__main__":
    unittest.main()
