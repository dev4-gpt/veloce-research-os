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
        self.assertIn("/knowledge_graph_status", paths)
        self.assertIn("/knowledge_graph_query", paths)
        self.assertIn("/knowledge_memory_record", paths)

    def test_knowledge_graph_query_prefers_docs_by_default(self) -> None:
        temp = tempfile.TemporaryDirectory()
        original_graph = app.GRAPHIFY_GRAPH_PATH
        try:
            graph_path = Path(temp.name) / "graph.json"
            graph_path.write_text(
                json.dumps(
                    {
                        "built_at_commit": "abc123",
                        "nodes": [
                            {
                                "id": "v19_product",
                                "label": "V1.9 OpenWebUI Hermes Ruflo Paperclip MCPO Obsidian Graphify Product Plan",
                                "source_file": "docs/v1.9-full-capability-agentic-product-plan.md",
                                "community": 1,
                            },
                            {
                                "id": "v19_graph",
                                "label": "V1.9J Obsidian Graphify Knowledge Graph Memory Loop",
                                "source_file": "docs/v1.9J-knowledge-graph-memory-loop.md",
                                "community": 1,
                            },
                            {
                                "id": "operating_graph",
                                "label": "Veloce Operating Graph",
                                "source_file": "knowledge/graph-memory/veloce-operating-graph.md",
                                "community": 4,
                            },
                            {
                                "id": "manifest_mcpo_paths",
                                "label": "mcpo_paths",
                                "source_file": "knowledge/graph-memory/manifest.json",
                                "source_location": "L11",
                                "community": 4,
                            },
                            {
                                "id": "v19l",
                                "label": "V1.9L Operating Graph Ingestion Layer",
                                "source_file": "docs/v1.9L-operating-graph-ingestion.md",
                                "community": 4,
                            },
                            {
                                "id": "ruflo_test",
                                "label": ".test_ruflo_execution_packet_returns_paperclip_handoff()",
                                "source_file": "tools/mcpo-openwebui-proxy/tests/test_ruflo_status.py",
                                "source_location": "L160",
                                "community": 2,
                            },
                            {
                                "id": "ruflo_code",
                                "label": "mcpo_ruflo_tool.py",
                                "source_file": "tools/openwebui/mcpo_ruflo_tool.py",
                                "community": 3,
                            },
                        ],
                        "links": [
                            {
                                "source": "v19_product",
                                "target": "v19_graph",
                                "relation": "references",
                                "source_file": "docs/v1.9-full-capability-agentic-product-plan.md",
                            },
                            {
                                "source": "operating_graph",
                                "target": "v19l",
                                "relation": "references",
                                "source_file": "knowledge/graph-memory/veloce-operating-graph.md",
                            },
                            {
                                "source": "manifest_mcpo_paths",
                                "target": "operating_graph",
                                "relation": "summarizes",
                                "source_file": "knowledge/graph-memory/manifest.json",
                            },
                            {
                                "source": "ruflo_test",
                                "target": "ruflo_code",
                                "relation": "calls",
                                "source_file": "tools/mcpo-openwebui-proxy/tests/test_ruflo_status.py",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            app.GRAPHIFY_GRAPH_PATH = graph_path
            status = app._knowledge_graph_status()
            self.assertTrue(status["ok"])
            self.assertEqual(status["nodes"], 7)

            result = app._knowledge_graph_query(
                {
                    "question": "what connects OpenWebUI, Hermes, Ruflo, Paperclip, MCPO, Obsidian, and Graphify?",
                    "max_results": 4,
                }
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["source_filter"], "docs")
            self.assertIn("v1.9N_weighted_docs", result["ranking_mode"])
            self.assertIn("summary_answer", result)
            self.assertIn("matches", result)
            self.assertIn("relationships", result)
            self.assertIn("evidence_docs", result)
            self.assertTrue(result["matches"])
            self.assertTrue(
                all(
                    item["source_file"].startswith(("docs/", "knowledge/graph-memory/"))
                    for item in result["matches"]
                )
            )
            self.assertEqual(
                result["matches"][0]["source_file"],
                "docs/v1.9-full-capability-agentic-product-plan.md",
            )
            self.assertIn(
                "docs/v1.9-full-capability-agentic-product-plan.md",
                result["evidence_docs"],
            )

            operating_result = app._knowledge_graph_query(
                {
                    "question": "what is the Veloce operating graph across Paperclip, Hermes, Ruflo, OpenWebUI, MCPO, Obsidian, and Graphify?",
                    "max_results": 4,
                    "source_filter": "docs",
                }
            )
            self.assertTrue(operating_result["ok"])
            self.assertEqual(operating_result["source_filter"], "docs")
            self.assertIn("v1.9N_weighted_docs", operating_result["ranking_mode"])
            self.assertEqual(
                operating_result["matches"][0]["source_file"],
                "knowledge/graph-memory/veloce-operating-graph.md",
            )
            self.assertNotIn(
                "knowledge/graph-memory/manifest.json",
                {item["source_file"] for item in operating_result["matches"]},
            )
            self.assertIn(
                "knowledge/graph-memory/veloce-operating-graph.md",
                operating_result["evidence_docs"],
            )

            knowledge_result = app._knowledge_graph_query(
                {
                    "question": "operating graph",
                    "max_results": 4,
                    "source_filter": "knowledge",
                }
            )
            self.assertTrue(knowledge_result["ok"])
            self.assertEqual(knowledge_result["source_filter"], "knowledge")
            self.assertEqual(
                knowledge_result["matches"][0]["source_file"],
                "knowledge/graph-memory/veloce-operating-graph.md",
            )
            self.assertTrue(
                all(
                    item["source_file"].startswith("knowledge/graph-memory/")
                    for item in knowledge_result["matches"]
                )
            )

            tests_result = app._knowledge_graph_query(
                {
                    "question": "which tests prove Ruflo execution packet handoff?",
                    "max_results": 4,
                    "source_filter": "tests",
                }
            )
            self.assertTrue(tests_result["ok"])
            self.assertEqual(tests_result["source_filter"], "tests")
            self.assertEqual(
                tests_result["matches"][0]["source_file"],
                "tools/mcpo-openwebui-proxy/tests/test_ruflo_status.py",
            )

            invalid_filter_result = app._knowledge_graph_query(
                {
                    "question": "how does graph memory connect to the product?",
                    "source_filter": "nonsense",
                }
            )
            self.assertTrue(invalid_filter_result["ok"])
            self.assertEqual(invalid_filter_result["source_filter"], "docs")
        finally:
            app.GRAPHIFY_GRAPH_PATH = original_graph
            temp.cleanup()

    def test_knowledge_memory_record_blocks_secret_like_content(self) -> None:
        result = app._knowledge_memory_record(
            {
                "source_system": "openwebui",
                "event_type": "tool_call",
                "summary": "Bearer abcdefghijklmnopqrstuvwxyz should not be recorded",
            }
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["decision"], "blocked_secret_like_content")

    def test_knowledge_memory_record_returns_obsidian_packet(self) -> None:
        result = app._knowledge_memory_record(
            {
                "source_system": "openwebui",
                "event_type": "tool_call",
                "summary": "User queried Veloce Graphify status from chat.",
                "tags": ["graphify", "openwebui"],
                "evidence_refs": ["docs/v1.9I-graphify-vps-proof.md"],
                "dry_run": True,
            }
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["decision"], "memory_record_ready")
        self.assertFalse(result["record_written"])
        self.assertIn("Obsidian human memory", result["obsidian_markdown"])


if __name__ == "__main__":
    unittest.main()
