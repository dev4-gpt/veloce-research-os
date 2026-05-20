#!/usr/bin/env python3
"""Export secret-free Veloce operating-system memory for Obsidian and Graphify."""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any


SECRET_PATTERN = re.compile(
    r"(api[_-]?key|secret|password|token|bearer\s+[a-z0-9_.-]{20,}|sk-[a-z0-9]{20,})",
    re.IGNORECASE,
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _sanitize(value: Any, limit: int = 240) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    text = SECRET_PATTERN.sub("[redacted]", text)
    text = re.sub(r"\s+", " ", text)
    return text[:limit]


def _git_commit(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except OSError:
        return "unknown"


def _frontmatter(title: str, tags: list[str], source_system: str, commit: str) -> str:
    tag_text = ", ".join(tags)
    return (
        "---\n"
        f"title: {title}\n"
        f"source_system: {source_system}\n"
        f"generated_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
        f"commit: {commit}\n"
        f"tags: [{tag_text}]\n"
        "---\n\n"
    )


def _write_markdown(path: Path, title: str, tags: list[str], source_system: str, body: str, commit: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_frontmatter(title, tags, source_system, commit) + body.rstrip() + "\n", encoding="utf-8")


def _python_functions(path: Path) -> list[str]:
    try:
        tree = ast.parse(_read(path))
    except SyntaxError:
        return []
    names = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)
    return sorted(set(names))


def _openapi_paths(app_path: Path) -> list[str]:
    text = _read(app_path)
    return sorted(set(re.findall(r'"(/[^"]+)":\s*\{', text)))


def _docs_matching(root: Path, *terms: str) -> list[str]:
    docs = []
    for path in sorted((root / "docs").glob("*.md")):
        text = (_read(path) + " " + path.name).lower()
        if any(term.lower() in text for term in terms):
            docs.append(_rel(path, root))
    return docs


def _paperclip_records(path: Path | None) -> list[dict[str, str]]:
    if not path or not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue
        summary = " ".join(
            _sanitize(raw.get(key))
            for key in ("id", "title", "status", "disposition", "team", "project")
            if raw.get(key)
        )
        if SECRET_PATTERN.search(summary):
            continue
        records.append(
            {
                "id": _sanitize(raw.get("id", "paperclip-item")),
                "title": _sanitize(raw.get("title", "Untitled Paperclip item")),
                "status": _sanitize(raw.get("status") or raw.get("disposition") or "unknown"),
                "team": _sanitize(raw.get("team") or raw.get("project") or "Veloce"),
            }
        )
    return records[:100]


def export_graph_memory(repo_root: Path, out_dir: Path, paperclip_jsonl: Path | None = None) -> list[Path]:
    repo_root = repo_root.resolve()
    out_dir = out_dir.resolve()
    commit = _git_commit(repo_root)
    written: list[Path] = []

    app_path = repo_root / "tools/mcpo-openwebui-proxy/app.py"
    openwebui_tool = repo_root / "tools/openwebui/veloce_agentic_tool.py"
    openapi = _openapi_paths(app_path)
    veloce_tools = [name for name in _python_functions(openwebui_tool) if name.startswith("veloce_")]

    operating_body = """# Veloce Operating Graph

## Product Relationship

- OpenWebUI is the operator cockpit for chat-driven analysis and tool calls.
- Veloce Agentic Control exposes typed chat tools instead of raw production access.
- MCPO is the gateway that serves allowlisted endpoints to OpenWebUI.
- Graphify stores the machine-readable graph extracted from repo, docs, runbooks, and generated memory files.
- Obsidian is the human-readable vault layer for evidence, issue memory, and operating notes.
- Hermes provides memory and agent reasoning context.
- Ruflo provides planning and orchestration packets while production runtime remains gated.
- Paperclip is the work ledger for issues, tasks, dispositions, comments, and closeout evidence.
- GitHub is the source of truth for code, docs, deploy manifests, and reproducible runbooks.
- VPS runtime proves the deployed stack with health checks, rollback drills, and live tool responses.

## Graph Path

OpenWebUI -> Veloce Agentic Control -> MCPO -> Graphify graph.json -> evidence docs.

Obsidian -> markdown memory -> Graphify extraction -> OpenWebUI knowledge_graph_query.

Hermes/Ruflo -> consume returned graph context for reasoning, planning, and worker packets.
"""
    path = out_dir / "veloce-operating-graph.md"
    _write_markdown(path, "Veloce Operating Graph", ["veloce", "architecture", "graph-memory"], "veloce", operating_body, commit)
    written.append(path)

    tools_body = ["# OpenWebUI And MCPO Tool Surface", "", "## OpenWebUI Tool Methods", ""]
    tools_body.extend(f"- `{name}`" for name in veloce_tools)
    tools_body.extend(["", "## MCPO Endpoint Paths", ""])
    tools_body.extend(f"- `{path}`" for path in openapi if path not in {"/", "/healthz"})
    tools_body.extend(
        [
            "",
            "## Product Meaning",
            "",
            "OpenWebUI users analyze Veloce through this typed tool surface. The graph memory endpoints are the bridge from chat to Obsidian and Graphify.",
        ]
    )
    path = out_dir / "openwebui-mcpo-tool-surface.md"
    _write_markdown(path, "OpenWebUI MCPO Tool Surface", ["openwebui", "mcpo", "tools"], "openwebui", "\n".join(tools_body), commit)
    written.append(path)

    paperclip_docs = _docs_matching(repo_root, "paperclip")
    paperclip_items = _paperclip_records(paperclip_jsonl)
    ledger_body = ["# Paperclip Work Ledger", "", "## Role", "", "Paperclip is the issue, task, disposition, comment, and evidence ledger for Veloce.", "", "## Evidence Documents", ""]
    ledger_body.extend(f"- `{doc}`" for doc in paperclip_docs)
    ledger_body.extend(["", "## Exported Issue And Task Metadata", ""])
    if paperclip_items:
        ledger_body.extend(
            f"- `{item['id']}`: {item['title']} | status={item['status']} | team={item['team']}"
            for item in paperclip_items
        )
    else:
        ledger_body.append("- No live Paperclip issue export was supplied. Use `--paperclip-jsonl` with secret-free issue metadata to graph issues, tasks, teams, and dispositions.")
    path = out_dir / "paperclip-work-ledger.md"
    _write_markdown(path, "Paperclip Work Ledger", ["paperclip", "issues", "tasks", "evidence"], "paperclip", "\n".join(ledger_body), commit)
    written.append(path)

    hermes_docs = _docs_matching(repo_root, "hermes")
    ruflo_docs = _docs_matching(repo_root, "ruflo")
    skills_body = ["# Hermes And Ruflo Skills", "", "## Hermes Memory And Agent Layer", ""]
    skills_body.extend(f"- `{doc}`" for doc in hermes_docs)
    skills_body.extend(["", "## Ruflo Planning And Orchestration Layer", ""])
    skills_body.extend(f"- `{doc}`" for doc in ruflo_docs)
    skills_body.extend(
        [
            "",
            "## Runtime Boundary",
            "",
            "Hermes and Ruflo can receive graph query results as structured context. Ruflo runtime execution remains gated until capability, policy, audit, alerting, canary, rollback, and kill-switch controls are active.",
        ]
    )
    path = out_dir / "hermes-ruflo-skills.md"
    _write_markdown(path, "Hermes And Ruflo Skills", ["hermes", "ruflo", "skills", "orchestration"], "hermes-ruflo", "\n".join(skills_body), commit)
    written.append(path)

    graph_body = """# Obsidian And Graphify Memory Loop

## Human Layer

Obsidian stores readable markdown notes, issue evidence, runbooks, generated memory packets, and operator closeouts.

## Machine Layer

Graphify extracts a graph from code, docs, runbooks, and graph-memory markdown into `graphify-out/graph.json`.

Graph-memory markdown files are the preferred human-facing evidence nodes. `manifest.json` exists for automation bookkeeping and should not outrank markdown notes in normal product queries.

## Chat Layer

OpenWebUI calls `knowledge_graph_status`, `knowledge_graph_query`, and `knowledge_memory_record` through MCPO. The query endpoint uses docs-first ranking for product questions and can filter docs, code, tests, or all sources.

## Public Safety

Raw graph files should not be published to the public showcase until a separate redaction and public-safety scan exists.
"""
    path = out_dir / "obsidian-graphify-memory-loop.md"
    _write_markdown(path, "Obsidian And Graphify Memory Loop", ["obsidian", "graphify", "memory"], "obsidian-graphify", graph_body, commit)
    written.append(path)

    manifest = {
        "ok": True,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": commit,
        "out_dir": _rel(out_dir, repo_root),
        "files": [_rel(path, repo_root) for path in written],
        "paperclip_items": len(paperclip_items),
        "openwebui_tools": len(veloce_tools),
        "mcpo_paths": len(openapi),
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written.append(manifest_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--out", default="knowledge/graph-memory", type=Path)
    parser.add_argument("--paperclip-jsonl", type=Path, default=None)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    out_dir = args.out if args.out.is_absolute() else repo_root / args.out
    written = export_graph_memory(repo_root, out_dir, args.paperclip_jsonl)
    print(json.dumps({"ok": True, "written": [str(path) for path in written]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
