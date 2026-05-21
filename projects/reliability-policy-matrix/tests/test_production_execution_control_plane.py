from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from production_execution_control_plane import (  # noqa: E402
    _capability_decision,
    _validate_capabilities,
    run,
)


BASE_CONFIG = {
    "generated_json": "artifacts/derived/production_execution_v2_0.json",
    "generated_markdown": "artifacts/derived/production_execution_v2_0.md",
    "audit_ledger": "artifacts/derived/production_execution_audit_v2_0.jsonl",
    "job_dir": "artifacts/derived/v2_jobs",
    "mode": "dry_run",
    "issue_id": "VEL-test",
    "actor": "test-controller",
    "target_state": "operator_supervised_unattended_production",
    "kill_switch_path": "",
    "live_enable_env": "VELOCE_V2_LIVE",
    "live_enable_value": "1",
    "required_live_env": {
        "paperclip_writeback": ["PAPERCLIP_AUTOMATION_TOKEN"],
        "chat_to_pr": ["GITHUB_TOKEN"],
    },
    "policy": {
        "read_only": "allow",
        "comment_only": "allow_scoped",
        "low_risk_write": "pr_or_canary_only",
        "production_write": "canary_rollback_alert_required",
        "destructive": "human_approval_required",
        "secret_bearing": "human_approval_required",
    },
    "forbidden_capabilities": ["raw_docker_control"],
    "capabilities": [
        {
            "name": "paperclip_writeback",
            "risk": "comment_only",
            "enabled": True,
            "live_enabled": False,
            "rollback": "post correction comment",
        },
        {
            "name": "chat_to_pr",
            "risk": "low_risk_write",
            "enabled": True,
            "live_enabled": False,
            "rollback": "close PR",
        },
    ],
    "job_templates": [
        {
            "id": "job-1",
            "capability": "paperclip_writeback",
            "budget_minutes": 5,
            "max_attempts": 1,
            "heartbeat_seconds": 60,
        }
    ],
}


class ProductionExecutionControlPlaneTest(unittest.TestCase):
    def test_dry_run_passes_and_writes_job_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = dict(BASE_CONFIG)
            config.update(
                {
                    "generated_json": str(root / "report.json"),
                    "generated_markdown": str(root / "report.md"),
                    "audit_ledger": str(root / "audit.jsonl"),
                    "job_dir": str(root / "jobs"),
                }
            )
            config_path = root / "config.json"
            config_path.write_text(__import__("json").dumps(config), encoding="utf-8")

            report = run(config_path, environ={})

            self.assertTrue(report["ok"])
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["decisions"][0]["decision"], "dry_run_ready")
            self.assertTrue((root / "jobs/job-1.json").exists())
            self.assertTrue((root / "audit.jsonl").exists())

    def test_live_request_blocks_without_capability_enablement(self) -> None:
        decision = _capability_decision(
            BASE_CONFIG["capabilities"][0],
            BASE_CONFIG,
            live_requested=True,
            kill_switch_active=False,
            environ={"VELOCE_V2_LIVE": "1", "PAPERCLIP_AUTOMATION_TOKEN": "x"},
        )

        self.assertEqual(decision["decision"], "blocked_live_not_enabled")

    def test_live_request_blocks_missing_env(self) -> None:
        capability = dict(BASE_CONFIG["capabilities"][0])
        capability["live_enabled"] = True

        decision = _capability_decision(
            capability,
            BASE_CONFIG,
            live_requested=True,
            kill_switch_active=False,
            environ={"VELOCE_V2_LIVE": "1"},
        )

        self.assertEqual(decision["decision"], "blocked_missing_live_env")
        self.assertEqual(decision["missing_env"], ["PAPERCLIP_AUTOMATION_TOKEN"])

    def test_forbidden_capability_is_rejected(self) -> None:
        config = dict(BASE_CONFIG)
        config["capabilities"] = [
            {
                "name": "raw_docker_control",
                "risk": "production_write",
                "enabled": True,
                "live_enabled": False,
                "rollback": "none",
            }
        ]

        errors = _validate_capabilities(config)

        self.assertTrue(any("forbidden capabilities" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
