import json
import tempfile
import unittest
from pathlib import Path

from tools.knowledge.graph_memory_export import export_graph_memory


class GraphMemoryExportTests(unittest.TestCase):
    def test_export_writes_operating_graph_and_tool_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "docs").mkdir()
            (root / "docs/v1.9J-knowledge-graph-memory-loop.md").write_text(
                "OpenWebUI MCPO Graphify Obsidian Hermes Ruflo Paperclip",
                encoding="utf-8",
            )
            (root / "tools/mcpo-openwebui-proxy").mkdir(parents=True)
            (root / "tools/mcpo-openwebui-proxy/app.py").write_text(
                'SPEC = {"/knowledge_graph_query": {}, "/stack_status": {}}\n',
                encoding="utf-8",
            )
            (root / "tools/openwebui").mkdir(parents=True)
            (root / "tools/openwebui/veloce_agentic_tool.py").write_text(
                "class Tools:\n"
                "    async def veloce_stack_status(self):\n"
                "        pass\n"
                "    async def veloce_knowledge_graph_query(self):\n"
                "        pass\n",
                encoding="utf-8",
            )

            written = export_graph_memory(root, root / "knowledge/graph-memory")
            rel = {path.relative_to(root).as_posix() for path in written}

            self.assertIn("knowledge/graph-memory/veloce-operating-graph.md", rel)
            self.assertIn("knowledge/graph-memory/openwebui-mcpo-tool-surface.md", rel)
            tool_surface = (root / "knowledge/graph-memory/openwebui-mcpo-tool-surface.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("veloce_knowledge_graph_query", tool_surface)
            self.assertIn("/knowledge_graph_query", tool_surface)

    def test_paperclip_jsonl_exports_secret_free_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "docs").mkdir()
            (root / "docs/paperclip-hermes-http-agent.md").write_text("Paperclip Hermes", encoding="utf-8")
            (root / "tools/mcpo-openwebui-proxy").mkdir(parents=True)
            (root / "tools/mcpo-openwebui-proxy/app.py").write_text("SPEC = {}\n", encoding="utf-8")
            (root / "tools/openwebui").mkdir(parents=True)
            (root / "tools/openwebui/veloce_agentic_tool.py").write_text("class Tools:\n    pass\n", encoding="utf-8")
            paperclip_jsonl = root / "paperclip.jsonl"
            paperclip_jsonl.write_text(
                json.dumps(
                    {
                        "id": "VEL-1",
                        "title": "Wire graph memory into OpenWebUI",
                        "status": "done",
                        "team": "AI Ops",
                    }
                )
                + "\n"
                + json.dumps(
                    {
                        "id": "VEL-2",
                        "title": "Bearer abcdefghijklmnopqrstuvwxyz should redact",
                        "status": "blocked",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            export_graph_memory(root, root / "knowledge/graph-memory", paperclip_jsonl)
            ledger = (root / "knowledge/graph-memory/paperclip-work-ledger.md").read_text(encoding="utf-8")

            self.assertIn("VEL-1", ledger)
            self.assertIn("Wire graph memory into OpenWebUI", ledger)
            self.assertNotIn("abcdefghijklmnopqrstuvwxyz", ledger)


if __name__ == "__main__":
    unittest.main()
