from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from autonomous_rollback_proof import run  # noqa: E402


def _config(root: Path) -> dict:
    return {
        "generated_json": str(root / "rollback.json"),
        "generated_markdown": str(root / "rollback.md"),
        "audit_ledger": str(root / "audit.jsonl"),
        "memory_markdown": str(root / "memory.md"),
        "rollback_packet": str(root / "rollback_packet.json"),
        "verification_packet": str(root / "verification_packet.json"),
        "alert_packet": str(root / "alert_packet.json"),
        "mode": "dry_run",
        "issue_id": "VEL-test",
        "actor": "test",
        "live_enable_env": "VELOCE_ROLLBACK_LIVE",
        "live_enable_value": "1",
        "live_enabled": False,
        "required_live_env": ["VELOCE_ROLLBACK_APPROVED"],
        "rollback_id": "v2e-test-rollback",
        "target_environment": "production",
        "last_known_good_ref": "lkg",
        "rollback_strategy": "restore_last_known_good_and_verify_stack_health",
        "pre_checks": ["stack_status"],
        "post_checks": ["stack_status"],
        "alert_channels": ["audit_ledger"],
    }


class AutonomousRollbackProofTest(unittest.TestCase):
    def test_dry_run_writes_rollback_verification_alert_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(config_path, environ={})

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "dry_run_ready")
            self.assertEqual(report["rollback_result"]["decision"], "written_dry_run")
            self.assertFalse(report["production_rollback_performed"])
            self.assertTrue((root / "rollback_packet.json").exists())
            self.assertTrue((root / "verification_packet.json").exists())
            self.assertTrue((root / "alert_packet.json").exists())
            self.assertIn("Autonomous Rollback", (root / "memory.md").read_text(encoding="utf-8"))

    def test_live_request_blocks_when_not_live_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(config_path, environ={"VELOCE_ROLLBACK_LIVE": "1", "VELOCE_ROLLBACK_APPROVED": "1"})

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_live_not_enabled")
            self.assertEqual(report["rollback_result"]["decision"], "blocked_not_written")
            self.assertFalse((root / "rollback_packet.json").exists())

    def test_live_request_blocks_when_approval_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config["live_enabled"] = True
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            report = run(config_path, environ={"VELOCE_ROLLBACK_LIVE": "1"})

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_missing_env")
            self.assertEqual(report["missing_env"], ["VELOCE_ROLLBACK_APPROVED"])


if __name__ == "__main__":
    unittest.main()
