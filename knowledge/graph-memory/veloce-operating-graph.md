---
title: Veloce Operating Graph
source_system: veloce
generated_at: 2026-05-21T19:45:09Z
commit: 45d2829
tags: [veloce, architecture, graph-memory]
---

# Veloce Operating Graph

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
- V2.0 Production Execution Control Plane creates typed capability decisions, job packets, and audit records for Paperclip writeback, chat-to-PR, canary deploy, rollback, alerting, and long-running agent jobs.
- V2.0A Paperclip Scoped Writeback Proof narrows the first live write path to one issue comment and one disposition update with explicit live gates, audit JSONL, rollback notes, and graph-memory markdown.

## Graph Path

OpenWebUI -> Veloce Agentic Control -> MCPO -> Graphify graph.json -> evidence docs.

Obsidian -> markdown memory -> Graphify extraction -> OpenWebUI knowledge_graph_query.

Hermes/Ruflo -> consume returned graph context for reasoning, planning, and worker packets.

V2.0 execution -> capability decision -> job packet -> audit ledger -> verification -> rollback/alert/disposition -> graph memory.

V2.0A Paperclip writeback -> scoped issue comment -> scoped disposition update -> audit JSONL -> Obsidian/Graphify memory.
