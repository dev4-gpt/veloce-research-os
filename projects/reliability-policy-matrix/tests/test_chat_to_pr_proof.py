from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from chat_to_pr_proof import run  # noqa: E402


def _config(root: Path) -> dict:
    return {
        "generated_json": str(root / "chat_to_pr.json"),
        "generated_markdown": str(root / "chat_to_pr.md"),
        "audit_ledger": str(root / "audit.jsonl"),
        "memory_markdown": str(root / "memory.md"),
        "mode": "dry_run",
        "issue_id": "VEL-test",
        "actor": "test",
        "live_enable_env": "VELOCE_CHAT_TO_PR_LIVE",
        "live_enable_value": "1",
        "live_enabled": False,
        "github_token_env": "GITHUB_TOKEN",
        "github_repository_env": "GITHUB_REPOSITORY",
        "github_api_base": "https://api.github.com",
        "base_branch": "main",
        "branch_prefix": "veloce/v2.0B-chat-to-pr",
        "allowed_file_prefixes": ["docs/"],
        "proof_file": "docs/v2.0B-chat-to-pr-live-proof.md",
        "commit_message": "docs: add v2.0B chat-to-PR live proof",
        "pr_title": "V2.0B Chat-to-PR Proof",
        "pr_body": "Proof PR",
        "proof_markdown": "# proof",
    }


class ChatToPrProofTest(unittest.TestCase):
    def test_dry_run_writes_audit_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(config_path, environ={})

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "dry_run_ready")
            self.assertEqual(report["branch_result"]["decision"], "not_sent_dry_run")
            self.assertEqual(report["file_result"]["decision"], "not_sent_dry_run")
            self.assertEqual(report["pr_result"]["decision"], "not_sent_dry_run")
            self.assertTrue((root / "audit.jsonl").exists())
            self.assertIn("Chat-to-PR Proof", (root / "memory.md").read_text(encoding="utf-8"))

    def test_live_request_blocks_when_not_live_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(
                config_path,
                environ={
                    "VELOCE_CHAT_TO_PR_LIVE": "1",
                    "GITHUB_TOKEN": "token",
                    "GITHUB_REPOSITORY": "owner/repo",
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

            report = run(config_path, environ={"VELOCE_CHAT_TO_PR_LIVE": "1"})

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_missing_env")
            self.assertEqual(report["missing_env"], ["GITHUB_TOKEN", "GITHUB_REPOSITORY"])

    def test_disallowed_file_blocks_before_live(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config["proof_file"] = "scripts/unsafe.py"
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            report = run(config_path, environ={})

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_disallowed_file")


if __name__ == "__main__":
    unittest.main()
