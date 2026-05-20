---
title: Veloce Operating Graph
source_system: veloce
generated_at: 2026-05-20T21:23:34Z
commit: 98f1e06
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

## Graph Path

OpenWebUI -> Veloce Agentic Control -> MCPO -> Graphify graph.json -> evidence docs.

Obsidian -> markdown memory -> Graphify extraction -> OpenWebUI knowledge_graph_query.

Hermes/Ruflo -> consume returned graph context for reasoning, planning, and worker packets.
