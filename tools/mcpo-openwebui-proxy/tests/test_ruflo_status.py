from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app  # noqa: E402


class RufloStatusTests(unittest.TestCase):
    def test_ruflo_status_reports_hardened_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sandbox = root / "sandbox"
            repo = root / "repo"
            (sandbox / ".claude-flow").mkdir(parents=True)
            (sandbox / ".claude").mkdir()
            (sandbox / ".agents").mkdir()
            (repo / "docs").mkdir(parents=True)

            (sandbox / ".claude-flow" / "config.yaml").write_text(
                "\n".join(
                    [
                        "swarm:",
                        "  maxAgents: 1",
                        "  autoScale: false",
                        "hooks:",
                        "  autoExecute: false",
                        "mcp:",
                        "  autoStart: false",
                    ]
                ),
                encoding="utf-8",
            )
            (sandbox / ".claude" / "settings.json").write_text(
                json.dumps(
                    {
                        "permissions": {
                            "allow": [],
                            "deny": ["Bash(*)", "Write(*)", "Edit(*)"],
                        },
                        "env": {
                            "CLAUDE_FLOW_V3_ENABLED": "false",
                            "CLAUDE_FLOW_HOOKS_ENABLED": "false",
                        },
                        "claudeFlow": {
                            "enabled": False,
                            "daemon": {"autoStart": False},
                        },
                    }
                ),
                encoding="utf-8",
            )
            (sandbox / ".agents" / "config.toml").write_text(
                '\n'.join(
                    [
                        'approval_policy = "on-request"',
                        'sandbox_mode = "workspace-write"',
                        'exclude = ["*_KEY", "*_SECRET"]',
                    ]
                ),
                encoding="utf-8",
            )
            (sandbox / ".mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "ruflo": {
                                "autoStart": False,
                                "env": {
                                    "CLAUDE_FLOW_HOOKS_ENABLED": "false",
                                    "CLAUDE_FLOW_MAX_AGENTS": "1",
                                },
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            (sandbox / "AGENTS.md").write_text("agents", encoding="utf-8")
            (sandbox / "CLAUDE.md").write_text("claude", encoding="utf-8")
            (repo / "docs" / "v1.6-ruflo-planning-closeout.md").write_text(
                "PYTHONPATH=. pytest -q\n3 passed in 0.01s\n",
                encoding="utf-8",
            )

            original_sandbox = app.RUFLO_SANDBOX_PATH
            original_repo = app.RESEARCH_REPO_PATH
            try:
                app.RUFLO_SANDBOX_PATH = sandbox
                app.RESEARCH_REPO_PATH = repo
                result = app._ruflo_status()
            finally:
                app.RUFLO_SANDBOX_PATH = original_sandbox
                app.RESEARCH_REPO_PATH = original_repo

        self.assertTrue(result["ok"])
        self.assertFalse(result["production_enabled"])
        self.assertEqual(result["mode"], "read_only_status")
        self.assertTrue(result["checks"]["runtime_hardened"]["ok"])
        self.assertTrue(result["checks"]["vel_124_validation"]["ok"])


if __name__ == "__main__":
    unittest.main()
