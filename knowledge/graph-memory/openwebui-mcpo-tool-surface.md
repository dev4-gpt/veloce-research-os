---
title: OpenWebUI MCPO Tool Surface
source_system: openwebui
generated_at: 2026-05-21T20:23:00Z
commit: 51536ed
tags: [openwebui, mcpo, tools]
---

# OpenWebUI And MCPO Tool Surface

## OpenWebUI Tool Methods

- `veloce_hermes_agent_task`
- `veloce_hermes_memory_query`
- `veloce_knowledge_graph_query`
- `veloce_knowledge_graph_status`
- `veloce_knowledge_memory_record`
- `veloce_repo_status`
- `veloce_ruflo_execution_packet`
- `veloce_ruflo_orchestration_dry_run`
- `veloce_ruflo_status`
- `veloce_stack_status`

## MCPO Endpoint Paths

- `/convert_time`
- `/get_current_time`
- `/hermes_agent_task`
- `/hermes_memory_query`
- `/knowledge_graph_query`
- `/knowledge_graph_status`
- `/knowledge_memory_record`
- `/repo_status`
- `/ruflo_execution_packet`
- `/ruflo_orchestration_dry_run`
- `/ruflo_plan`
- `/ruflo_status`
- `/stack_status`

## Product Meaning

OpenWebUI users analyze Veloce through this typed tool surface. The graph memory endpoints are the bridge from chat to Obsidian and Graphify. V2.0B extends the approved-chat path toward docs-only GitHub pull requests; V2.0C adds the heartbeat and stale-job controls needed before canary execution.
