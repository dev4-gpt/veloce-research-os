from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from canary_deploy_proof import run  # noqa: E402


def _config(root: Path) -> dict:
    return {
        "generated_json": str(root / "canary.json"),
        "generated_markdown": str(root / "canary.md"),
        "audit_ledger": str(root / "audit.jsonl"),
        "memory_markdown": str(root / "memory.md"),
        "canary_packet": str(root / "canary_packet.json"),
        "rollback_packet": str(root / "rollback_packet.json"),
        "alert_packet": str(root / "alert_packet.json"),
        "mode": "dry_run",
        "issue_id": "VEL-test",
        "actor": "test",
        "live_enable_env": "VELOCE_CANARY_DEPLOY_LIVE",
        "live_enable_value": "1",
        "live_enabled": False,
        "required_live_env": ["VELOCE_CANARY_APPROVED"],
        "candidate_id": "v2d-test-candidate",
        "candidate_kind": "noop_compose_candidate",
        "candidate_description": "test canary",
        "target_environment": "canary",
        "pre_health_checks": ["stack_status", "repo_status"],
        "post_health_checks": ["stack_status", "repo_status"],
        "rollback_strategy": "restore_last_known_good_and_verify_stack_health",
        "alert_channels": ["audit_ledger"],
    }


class CanaryDeployProofTest(unittest.TestCase):
    def test_dry_run_writes_packets_audit_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(config_path, environ={})

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "dry_run_ready")
            self.assertEqual(report["canary_result"]["decision"], "written_dry_run")
            self.assertFalse(report["production_mutation_performed"])
            self.assertTrue((root / "canary_packet.json").exists())
            self.assertTrue((root / "rollback_packet.json").exists())
            self.assertTrue((root / "alert_packet.json").exists())
            self.assertTrue((root / "audit.jsonl").exists())
            self.assertIn("Chat-to-Canary Deploy", (root / "memory.md").read_text(encoding="utf-8"))

    def test_live_request_blocks_when_not_live_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(config_path, environ={"VELOCE_CANARY_DEPLOY_LIVE": "1", "VELOCE_CANARY_APPROVED": "1"})

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_live_not_enabled")
            self.assertEqual(report["canary_packet"]["status"], "blocked")
            self.assertEqual(report["canary_result"]["decision"], "blocked_not_written")
            self.assertFalse((root / "canary_packet.json").exists())

    def test_live_request_blocks_when_approval_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config["live_enabled"] = True
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            report = run(config_path, environ={"VELOCE_CANARY_DEPLOY_LIVE": "1"})

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_missing_env")
            self.assertEqual(report["missing_env"], ["VELOCE_CANARY_APPROVED"])

    def test_live_ready_when_enabled_and_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config["live_enabled"] = True
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            report = run(
                config_path,
                environ={"VELOCE_CANARY_DEPLOY_LIVE": "1", "VELOCE_CANARY_APPROVED": "1"},
            )

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "live_ready")
            self.assertEqual(report["canary_result"]["decision"], "written_live_ready")
            self.assertFalse(report["production_mutation_performed"])


if __name__ == "__main__":
    unittest.main()
