from pathlib import Path
import json
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from production_ai_os_pilot_pack import _redact  # noqa: E402
from production_ai_os_pilot_pack import run  # noqa: E402


class ProductionAiOsPilotPackTest(unittest.TestCase):
    def _write_config(self, root: Path) -> Path:
        paperclip = {
            "generated_json": str(root / "paperclip.json"),
            "generated_markdown": str(root / "paperclip.md"),
            "audit_ledger": str(root / "paperclip.jsonl"),
            "memory_markdown": str(root / "paperclip-memory.md"),
            "issue_id": "VEL-test",
            "actor": "test",
            "live_enabled": False,
            "comment_endpoint_template": "/api/issues/{issue_id}/comments",
            "disposition_endpoint_template": "/api/issues/{issue_id}",
            "comment_markdown": "dry run",
        }
        chat = {
            "generated_json": str(root / "chat.json"),
            "generated_markdown": str(root / "chat.md"),
            "audit_ledger": str(root / "chat.jsonl"),
            "memory_markdown": str(root / "chat-memory.md"),
            "issue_id": "VEL-test",
            "actor": "test",
            "live_enabled": False,
            "proof_file": "docs/test.md",
            "proof_markdown": "test",
            "allowed_file_prefixes": ["docs/"],
        }
        (root / "paperclip_config.json").write_text(json.dumps(paperclip), encoding="utf-8")
        (root / "chat_config.json").write_text(json.dumps(chat), encoding="utf-8")
        config = {
            "generated_json": str(root / "pack.json"),
            "generated_markdown": str(root / "pack.md"),
            "audit_ledger": str(root / "pack.jsonl"),
            "memory_markdown": str(root / "pack-memory.md"),
            "mode": "dry_run",
            "issue_id": "VEL-pack",
            "actor": "test",
            "global_live_enable_env": "VELOCE_PRODUCTION_AI_OS_LIVE",
            "global_live_enable_value": "1",
            "stages": [
                {
                    "id": "v2.6",
                    "capability": "paperclip_writeback",
                    "config": str(root / "paperclip_config.json"),
                    "live_enable_env": "VELOCE_PAPERCLIP_WRITEBACK_LIVE",
                    "required_live_env": ["PAPERCLIP_BASE_URL", "PAPERCLIP_AUTOMATION_TOKEN"],
                    "live_enabled": False,
                },
                {
                    "id": "v2.7",
                    "capability": "chat_to_pr",
                    "config": str(root / "chat_config.json"),
                    "live_enable_env": "VELOCE_CHAT_TO_PR_LIVE",
                    "required_live_env": ["GITHUB_TOKEN", "GITHUB_REPOSITORY"],
                    "live_enabled": False,
                },
                {
                    "id": "v2.9",
                    "capability": "active_alerting",
                    "adapter_id": "alert_webhook",
                    "live_enable_env": "VELOCE_ALERT_LIVE",
                    "required_live_env": ["VELOCE_ALERT_WEBHOOK"],
                    "live_enabled": False,
                },
                {
                    "id": "v3.0",
                    "capability": "chat_to_canary_deploy",
                    "adapter_id": "canary_health_gate",
                    "live_enable_env": "VELOCE_CANARY_DEPLOY_LIVE",
                    "required_live_env": ["VELOCE_CANARY_APPROVED"],
                    "live_enabled": False,
                },
                {
                    "id": "v3.1",
                    "capability": "autonomous_rollback",
                    "adapter_id": "rollback_drill",
                    "live_enable_env": "VELOCE_ROLLBACK_LIVE",
                    "required_live_env": ["VELOCE_ROLLBACK_APPROVED"],
                    "live_enabled": False,
                },
            ],
        }
        path = root / "pack_config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def test_dry_run_pack_passes_without_live_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(Path(tmp))

            report = run(path, environ={})

            self.assertTrue(report["ok"])
            self.assertEqual(report["status"], "pass")
            self.assertTrue(all(stage["decision"] == "dry_run_ready" for stage in report["stages"]))
            self.assertTrue(Path(report["memory_markdown"]).exists())

    def test_live_flags_block_when_stage_not_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write_config(Path(tmp))

            report = run(
                path,
                environ={
                    "VELOCE_PRODUCTION_AI_OS_LIVE": "1",
                    "VELOCE_ALERT_LIVE": "1",
                    "VELOCE_ALERT_WEBHOOK": "https://example.invalid/hook",
                },
            )

            alert = [stage for stage in report["stages"] if stage["id"] == "v2.9"][0]
            self.assertFalse(report["ok"])
            self.assertEqual(alert["decision"], "blocked_live_not_enabled")

    def test_redaction_keeps_secret_free_marker(self) -> None:
        redacted = _redact(
            {
                "secret_free": True,
                "paperclip_token": "sensitive",
                "nested": {"webhook_url": "sensitive"},
            }
        )

        self.assertTrue(redacted["secret_free"])
        self.assertEqual(redacted["paperclip_token"], "[redacted]")
        self.assertEqual(redacted["nested"]["webhook_url"], "[redacted]")


if __name__ == "__main__":
    unittest.main()
