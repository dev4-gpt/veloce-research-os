---
title: Veloce Operating Graph
source_system: veloce
generated_at: 2026-05-22T19:00:40Z
commit: 6560e6b
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
- V2.0B Chat-to-PR Proof narrows the first GitHub write path to one generated branch, one docs-only file update, one pull request, audit JSONL, and graph-memory markdown.
- V2.0C Long-Running Job Heartbeat Proof narrows unattended work to one resumable job packet, one heartbeat record, stale-job detection, audit JSONL, and graph-memory markdown.
- V2.0D Chat-to-Canary Deploy Proof narrows canary deploy to one no-op candidate, pre/post health snapshots, rollback packet, alert packet, audit JSONL, and graph-memory markdown with no production mutation.
- V2.0E Autonomous Rollback Proof narrows rollback to one rollback packet, pre/post verification packet, alert packet, audit JSONL, and graph-memory markdown with no destructive production command.
- V2.0F Paperclip Live Writeback Pilot narrows the first live Paperclip pilot to one scoped issue comment and one disposition update behind explicit env gates and local live config.
- V2.0G Chat-to-PR Live Pilot narrows the first live GitHub pilot to one docs-only branch, file update, pull request, audit JSONL, and graph-memory markdown.
- V2.0H Canary Deploy Live Pilot narrows canary promotion to an operator-approved candidate packet with rollback approval, health snapshots, alert packet, and audit JSONL.
- V2.0I Long-Running Agent Runner narrows agent orchestration to lease acquisition, bounded step planning, heartbeat records, cancellation packet, audit JSONL, and graph-memory markdown.
- V2.1-V2.5 Production AI OS Completion adds a typed MCPO execution API, durable file-backed runner, job status/approve/cancel endpoints, audit tails, packet schemas, redaction checks, trace IDs, and graph-memory event ingestion.

## Graph Path

OpenWebUI -> Veloce Agentic Control -> MCPO -> Graphify graph.json -> evidence docs.

Obsidian -> markdown memory -> Graphify extraction -> OpenWebUI knowledge_graph_query.

Hermes/Ruflo -> consume returned graph context for reasoning, planning, and worker packets.

V2.0 execution -> capability decision -> job packet -> audit ledger -> verification -> rollback/alert/disposition -> graph memory.

V2.0A Paperclip writeback -> scoped issue comment -> scoped disposition update -> audit JSONL -> Obsidian/Graphify memory.

V2.0B chat-to-PR -> generated branch -> docs-only proof file -> pull request -> audit JSONL -> Obsidian/Graphify memory.

V2.0C long-running jobs -> job packet -> heartbeat ledger -> stale-job detector -> audit JSONL -> Obsidian/Graphify memory.

V2.0D chat-to-canary -> no-op candidate -> pre/post health snapshots -> rollback packet -> alert packet -> audit JSONL -> Obsidian/Graphify memory.

V2.0E autonomous rollback -> rollback packet -> verification packet -> alert packet -> audit JSONL -> Obsidian/Graphify memory.

V2.0F Paperclip live pilot -> scoped issue comment -> scoped disposition update -> audit JSONL -> Obsidian/Graphify memory.

V2.0G chat-to-PR live pilot -> generated branch -> docs-only proof file -> pull request -> audit JSONL -> Obsidian/Graphify memory.

V2.0H canary live pilot -> approved candidate -> pre/post health snapshots -> rollback approval -> alert packet -> audit JSONL -> Obsidian/Graphify memory.

V2.0I agent runner -> lease -> bounded steps -> heartbeat ledger -> cancellation packet -> audit JSONL -> Obsidian/Graphify memory.

V2.1-V2.5 execution API -> typed enqueue/status/approve/cancel -> durable runner -> lease/heartbeat/idempotency -> audit tail -> graph-memory event -> OpenWebUI knowledge query.
