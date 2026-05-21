from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from paperclip_writeback_proof import run  # noqa: E402


def _config(root: Path) -> dict:
    return {
        "generated_json": str(root / "paperclip.json"),
        "generated_markdown": str(root / "paperclip.md"),
        "audit_ledger": str(root / "audit.jsonl"),
        "memory_markdown": str(root / "memory.md"),
        "mode": "dry_run",
        "issue_id": "VEL-test",
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
        "comment_markdown": "V2.0A proof comment",
    }


class PaperclipWritebackProofTest(unittest.TestCase):
    def test_dry_run_writes_audit_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(config_path, environ={})

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "dry_run_ready")
            self.assertEqual(report["comment_result"]["decision"], "not_sent_dry_run")
            self.assertTrue((root / "audit.jsonl").exists())
            self.assertIn("Paperclip Scoped Writeback", (root / "memory.md").read_text(encoding="utf-8"))

    def test_live_request_blocks_when_not_live_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(
                config_path,
                environ={
                    "VELOCE_PAPERCLIP_WRITEBACK_LIVE": "1",
                    "PAPERCLIP_BASE_URL": "https://paperclip.example",
                    "PAPERCLIP_AUTOMATION_TOKEN": "token",
                },
            )

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_live_not_enabled")

    def test_live_request_blocks_when_env_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config["live_enabled"] = True
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            report = run(config_path, environ={"VELOCE_PAPERCLIP_WRITEBACK_LIVE": "1"})

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_missing_env")
            self.assertEqual(report["missing_env"], ["PAPERCLIP_BASE_URL", "PAPERCLIP_AUTOMATION_TOKEN"])


if __name__ == "__main__":
    unittest.main()
