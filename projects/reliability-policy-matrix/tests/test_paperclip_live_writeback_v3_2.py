from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import paperclip_live_writeback_v3_2 as v32  # noqa: E402


def _config(root: Path) -> dict:
    return {
        "generated_json": str(root / "v32.json"),
        "generated_markdown": str(root / "v32.md"),
        "audit_ledger": str(root / "v32.jsonl"),
        "memory_markdown": str(root / "v32-memory.md"),
        "rollback_packet": str(root / "v32-rollback.json"),
        "local_live_config": str(root / "v32-live.local.json"),
        "effective_paperclip_config": str(root / "v32-effective.local.json"),
        "base_config": str(root / "base.json"),
        "mode": "dry_run",
        "proof_title": "V3.2 Paperclip Live Writeback",
        "action_id": "v3.2-paperclip-live-writeback",
        "issue_id": "VEL-v2.0F-PILOT",
        "required_issue_id": "VEL-v2.0F-PILOT",
        "paperclip_pilot_issue_id_env": "PAPERCLIP_PILOT_ISSUE_ID",
        "actor": "test",
        "global_live_enable_env": "VELOCE_PRODUCTION_AI_OS_LIVE",
        "global_live_enable_value": "1",
        "live_enable_env": "VELOCE_PAPERCLIP_WRITEBACK_LIVE",
        "live_enable_value": "1",
        "live_enabled": False,
        "paperclip_base_url_env": "PAPERCLIP_BASE_URL",
        "paperclip_token_env": "PAPERCLIP_AUTOMATION_TOKEN",
        "issue_get_endpoint_template": "/api/issues/{issue_id}",
        "comment_endpoint_template": "/api/issues/{issue_id}/comments",
        "disposition_endpoint_template": "/api/issues/{issue_id}",
        "target_disposition": "in_review",
        "rollback_disposition": "in_review",
        "idempotency_marker": "V3.2 Paperclip live pilot",
        "restore_on_partial_failure": True,
        "allowed_statuses": [200, 201, 204],
        "comment_markdown": "pilot comment for VEL-v2.0F-PILOT",
    }


def _base(root: Path) -> dict:
    return {
        "generated_json": str(root / "base-report.json"),
        "generated_markdown": str(root / "base-report.md"),
        "audit_ledger": str(root / "base-audit.jsonl"),
        "memory_markdown": str(root / "base-memory.md"),
        "mode": "dry_run",
        "proof_title": "base",
        "action_id": "base",
        "issue_id": "VEL-v2.0F-PILOT",
        "actor": "test",
        "live_enable_env": "VELOCE_PAPERCLIP_WRITEBACK_LIVE",
        "live_enable_value": "1",
        "live_enabled": False,
        "paperclip_base_url_env": "PAPERCLIP_BASE_URL",
        "paperclip_token_env": "PAPERCLIP_AUTOMATION_TOKEN",
        "comment_endpoint_template": "/api/issues/{issue_id}/comments",
        "disposition_endpoint_template": "/api/issues/{issue_id}",
        "comment_method": "POST",
        "disposition_method": "PATCH",
        "comment_field": "body",
        "disposition_field": "disposition",
        "target_disposition": "in_review",
        "rollback_disposition": "in_review",
        "allowed_statuses": [200, 201, 204],
        "comment_markdown": "base comment",
    }


class PaperclipLiveWritebackV32Test(unittest.TestCase):
    def _write(self, root: Path, config: dict) -> Path:
        (root / "base.json").write_text(json.dumps(_base(root)), encoding="utf-8")
        path = root / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def test_dry_run_writes_local_config_with_idempotency_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write(root, _config(root))

            report = v32.run(path, environ={})

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "dry_run_ready")
            local = json.loads((root / "v32-live.local.json").read_text(encoding="utf-8"))
            effective = json.loads((root / "v32-effective.local.json").read_text(encoding="utf-8"))
            self.assertTrue(local["live_enabled"])
            self.assertIn("V3.2 Paperclip live pilot", effective["comment_markdown"])
            self.assertIn("Trace ID:", effective["comment_markdown"])

    def test_env_generated_issue_id_updates_local_and_effective_configs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write(root, _config(root))

            report = v32.run(path, environ={"PAPERCLIP_PILOT_ISSUE_ID": "VEL-145"})

            self.assertTrue(report["ok"])
            self.assertEqual(report["issue_id"], "VEL-145")
            self.assertEqual(report["required_issue_id"], "VEL-145")
            self.assertEqual(report["issue_id_source"], "env")
            local = json.loads((root / "v32-live.local.json").read_text(encoding="utf-8"))
            effective = json.loads((root / "v32-effective.local.json").read_text(encoding="utf-8"))
            self.assertEqual(local["issue_id"], "VEL-145")
            self.assertEqual(local["required_issue_id"], "VEL-145")
            self.assertEqual(effective["issue_id"], "VEL-145")
            self.assertIn("VEL-145", effective["comment_markdown"])
            self.assertNotIn("VEL-v2.0F-PILOT", effective["comment_markdown"])

    def test_invalid_env_issue_id_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write(root, _config(root))

            report = v32.run(path, environ={"PAPERCLIP_PILOT_ISSUE_ID": "../bad"})

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_invalid_paperclip_issue_id")
            self.assertFalse(report["issue_id_valid"])

    def test_rejects_wrong_issue_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config["issue_id"] = "VEL-145"
            path = self._write(root, config)

            report = v32.run(
                path,
                environ={"VELOCE_PRODUCTION_AI_OS_LIVE": "1", "VELOCE_PAPERCLIP_WRITEBACK_LIVE": "1"},
            )

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_wrong_issue_id")

    def test_blocks_live_when_env_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config["live_enabled"] = True
            path = self._write(root, config)

            report = v32.run(
                path,
                environ={"VELOCE_PRODUCTION_AI_OS_LIVE": "1", "VELOCE_PAPERCLIP_WRITEBACK_LIVE": "1"},
            )

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_missing_env")
            self.assertEqual(report["missing_env"], ["PAPERCLIP_BASE_URL", "PAPERCLIP_AUTOMATION_TOKEN"])

    def test_redaction_keeps_secret_free_marker(self) -> None:
        redacted = v32._redact({"secret_free": True, "paperclip_token": "secret", "authorization": "bearer"})

        self.assertTrue(redacted["secret_free"])
        self.assertEqual(redacted["paperclip_token"], "[redacted]")
        self.assertEqual(redacted["authorization"], "[redacted]")

    def test_partial_failure_emits_rollback_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config["live_enabled"] = True
            path = self._write(root, config)

            proof_report = {
                "ok": False,
                "decision": "live_ready",
                "comment_result": {"decision": "sent", "ok": True},
                "disposition_result": {"decision": "sent", "ok": False},
            }
            with mock.patch.object(v32, "_previous_issue_state", return_value={"previous_disposition": "todo"}):
                with mock.patch.object(v32, "_request_json", return_value={"ok": True, "status": 200}):
                    with mock.patch.object(v32.paperclip_writeback_proof, "run", return_value=proof_report):
                        report = v32.run(
                            path,
                            environ={
                                "VELOCE_PRODUCTION_AI_OS_LIVE": "1",
                                "VELOCE_PAPERCLIP_WRITEBACK_LIVE": "1",
                                "PAPERCLIP_BASE_URL": "https://paperclip.example",
                                "PAPERCLIP_AUTOMATION_TOKEN": "token",
                            },
                        )

            self.assertFalse(report["ok"])
            self.assertTrue(report["rollback_packet"]["partial_failure"])
            self.assertEqual(report["rollback_packet"]["decision"], "rollback_packet_ready")
            self.assertTrue((root / "v32-rollback.json").exists())


if __name__ == "__main__":
    unittest.main()
