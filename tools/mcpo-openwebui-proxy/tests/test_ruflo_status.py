from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app  # noqa: E402


class RufloStatusTests(unittest.TestCase):
    def _with_hardened_paths(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
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
        app.RUFLO_SANDBOX_PATH = sandbox
        app.RESEARCH_REPO_PATH = repo
        return temp, original_sandbox, original_repo

    def _restore_paths(self, temp, original_sandbox, original_repo) -> None:
        app.RUFLO_SANDBOX_PATH = original_sandbox
        app.RESEARCH_REPO_PATH = original_repo
        temp.cleanup()

    def test_ruflo_status_reports_hardened_sandbox(self) -> None:
        paths = self._with_hardened_paths()
        try:
            result = app._ruflo_status()
            self.assertTrue(result["ok"])
            self.assertFalse(result["production_enabled"])
            self.assertEqual(result["mode"], "read_only_status")
            self.assertTrue(result["checks"]["runtime_hardened"]["ok"])
            self.assertTrue(result["checks"]["vel_124_validation"]["ok"])
        finally:
            self._restore_paths(*paths)

    def test_ruflo_plan_returns_paperclip_ready_plan(self) -> None:
        paths = self._with_hardened_paths()
        try:
            result = app._ruflo_plan(
                {
                    "issue_id": "VEL-128",
                    "title": "Plan read-only Ruflo bridge",
                    "description": "Create an approval-gated plan for Paperclip.",
                    "assignee": "Technical Builder",
                    "requested_mode": "plan",
                }
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["service"], "veloce_ruflo_plan")
            self.assertEqual(result["decision"], "plan_only_ready")
            self.assertFalse(result["ruflo_runtime_invoked"])
            self.assertIn("paperclip_comment_markdown", result)
            self.assertIn("VEL-128", result["paperclip_comment_markdown"])
        finally:
            self._restore_paths(*paths)

    def test_ruflo_plan_blocks_execution_mode(self) -> None:
        result = app._ruflo_plan(
            {
                "title": "Deploy Ruflo",
                "description": "Start services now.",
                "requested_mode": "execute",
            }
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["decision"], "blocked_execution_request")
        self.assertFalse(result["ruflo_runtime_invoked"])

    def test_ruflo_execution_packet_requires_human_approval(self) -> None:
        result = app._ruflo_execution_packet(
            {
                "title": "Execute approved handoff",
                "description": "Create a Paperclip execution packet.",
                "requested_mode": "execution_packet",
            }
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["decision"], "blocked_missing_human_approval")
        self.assertFalse(result["ruflo_runtime_invoked"])

    def test_ruflo_execution_packet_returns_paperclip_handoff(self) -> None:
        paths = self._with_hardened_paths()
        try:
            result = app._ruflo_execution_packet(
                {
                    "issue_id": "VEL-128",
                    "title": "Execute approved Ruflo bridge verification",
                    "description": "Complete the Paperclip execution loop after human approval.",
                    "approved_by": "Aryaman",
                    "approval": "human_approved",
                    "execution_owner": "Codex/GitHub",
                    "requested_mode": "execution_packet",
                }
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["service"], "veloce_ruflo_execution_packet")
            self.assertEqual(result["decision"], "approval_gated_execution_packet_ready")
            self.assertFalse(result["ruflo_runtime_invoked"])
            self.assertIn("paperclip_comment_markdown", result)
            self.assertIn("VEL-128", result["paperclip_comment_markdown"])
            self.assertIn("verification_commands", result["execution_packet"])
        finally:
            self._restore_paths(*paths)

    def test_ruflo_execution_packet_blocks_runtime_execution(self) -> None:
        result = app._ruflo_execution_packet(
            {
                "title": "Start Ruflo runtime",
                "description": "Start autopilot now.",
                "approved_by": "Aryaman",
                "approval": "human_approved",
                "requested_mode": "execute",
            }
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["decision"], "blocked_runtime_execution_request")
        self.assertFalse(result["ruflo_runtime_invoked"])

    def test_hermes_memory_query_dry_run_is_structured(self) -> None:
        result = app._hermes_memory_query(
            {
                "query": "What is the current Veloce production posture?",
                "dry_run": True,
            }
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["service"], "veloce_hermes_memory_query")
        self.assertFalse(result["hermes_invoked"])
        self.assertTrue(result["audit"]["secret_free"])

    def test_hermes_agent_task_requires_task(self) -> None:
        result = app._hermes_agent_task({"context": "missing task"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["decision"], "invalid_input")

    def test_ruflo_orchestration_dry_run_returns_task_graph_and_denials(self) -> None:
        result = app._ruflo_orchestration_dry_run(
            {
                "issue_id": "VEL-200",
                "goal": "Plan a production deploy but do not read secrets or run docker exec.",
            }
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["decision"], "orchestration_dry_run_ready")
        self.assertFalse(result["ruflo_runtime_invoked"])
        self.assertGreaterEqual(len(result["task_graph"]), 1)
        denied = {item["capability"] for item in result["denied_capabilities"]}
        self.assertIn("secret_read", denied)
        self.assertIn("raw_docker_control", denied)

    def test_openapi_exposes_v19_paths(self) -> None:
        paths = app._openapi_spec()["paths"]

        self.assertIn("/hermes_memory_query", paths)
        self.assertIn("/hermes_agent_task", paths)
        self.assertIn("/ruflo_orchestration_dry_run", paths)


if __name__ == "__main__":
    unittest.main()
