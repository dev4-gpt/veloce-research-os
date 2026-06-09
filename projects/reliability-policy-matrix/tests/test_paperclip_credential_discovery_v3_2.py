from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import paperclip_credential_discovery_v3_2 as discovery  # noqa: E402


def _config(root: Path) -> dict:
    return {
        "generated_json": str(root / "discovery.json"),
        "generated_markdown": str(root / "discovery.md"),
        "audit_ledger": str(root / "discovery.jsonl"),
        "mode": "read_only",
        "issue_id": "VEL-v2.0F-PILOT",
        "paperclip_base_url_env": "PAPERCLIP_BASE_URL",
        "paperclip_token_env": "PAPERCLIP_AUTOMATION_TOKEN",
        "candidate_base_urls": [
            "https://paperclip.example",
            "https://paperclip.example/VEL",
        ],
        "issue_get_endpoint_template": "/api/issues/{issue_id}",
        "possible_api_statuses": [200, 401, 403, 405],
        "paperclip_container_hint": "paperclip-iraj-paperclip-1",
    }


class PaperclipCredentialDiscoveryV32Test(unittest.TestCase):
    def _write(self, root: Path, config: dict) -> Path:
        path = root / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def test_finds_likely_base_route_without_printing_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write(root, _config(root))

            with mock.patch.object(
                discovery,
                "_probe_url",
                side_effect=[
                    {"status": 404, "content_type": "text/html", "body_hash": "a", "error": "HTTPError"},
                    {"status": 401, "content_type": "application/json", "body_hash": "b", "error": "HTTPError"},
                ],
            ):
                report = discovery.run(path, environ={"PAPERCLIP_AUTOMATION_TOKEN": "secret-token"})

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "base_route_candidate_found_token_present")
            self.assertEqual(report["likely_base_url"], "https://paperclip.example/VEL")
            self.assertTrue(report["token_present"])
            self.assertFalse(report["token_value_printed"])
            self.assertNotIn("secret-token", (root / "discovery.json").read_text(encoding="utf-8"))
            self.assertNotIn("secret-token", (root / "discovery.md").read_text(encoding="utf-8"))

    def test_env_base_url_is_probed_first_and_deduped(self) -> None:
        config = _config(Path("/tmp"))
        candidates = discovery._candidate_base_urls(
            config,
            environ={"PAPERCLIP_BASE_URL": "https://paperclip.example/VEL/"},
        )

        self.assertEqual(candidates[0], "https://paperclip.example/VEL")
        self.assertEqual(candidates.count("https://paperclip.example/VEL"), 1)

    def test_unconfirmed_route_still_writes_operator_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write(root, _config(root))

            with mock.patch.object(
                discovery,
                "_probe_url",
                return_value={"status": 404, "content_type": "text/html", "body_hash": "a", "error": "HTTPError"},
            ):
                report = discovery.run(path, environ={})

            self.assertEqual(report["decision"], "base_route_unconfirmed")
            self.assertEqual(report["status"], "needs_inspection")
            self.assertGreaterEqual(len(report["vps_readonly_commands"]), 3)
            self.assertTrue((root / "discovery.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
