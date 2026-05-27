---
title: OpenWebUI MCPO Tool Surface
source_system: openwebui
generated_at: 2026-05-27T04:23:01Z
commit: 3b3311f
tags: [openwebui, mcpo, tools]
---

# OpenWebUI And MCPO Tool Surface

## OpenWebUI Tool Methods

- `veloce_hermes_agent_task`
- `veloce_hermes_memory_query`
- `veloce_knowledge_graph_query`
- `veloce_knowledge_graph_status`
- `veloce_knowledge_memory_record`
- `veloce_production_audit_tail`
- `veloce_production_execution_status`
- `veloce_production_job_approve`
- `veloce_production_job_cancel`
- `veloce_production_job_enqueue`
- `veloce_production_job_status`
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
- `/production_audit_tail`
- `/production_execution_status`
- `/production_job_approve`
- `/production_job_cancel`
- `/production_job_enqueue`
- `/production_job_status`
- `/repo_status`
- `/ruflo_execution_packet`
- `/ruflo_orchestration_dry_run`
- `/ruflo_plan`
- `/ruflo_status`
- `/stack_status`

## Product Meaning

OpenWebUI users analyze Veloce through this typed tool surface. The graph memory endpoints are the bridge from chat to Obsidian and Graphify. V2.0B extends the approved-chat path toward docs-only GitHub pull requests; V2.0C adds heartbeat and stale-job controls; V2.0D prepares no-op canary, rollback, and alert packets before production mutation is allowed. V2.0E-I complete the pilot pack with rollback proof, live Paperclip/PR/canary pilot configs, and a bounded agent runner. V2.1-V2.5 add typed production execution endpoints for status, enqueue, approve, cancel, and audit tail. V2.6-V3.1 adds a dry-run safe pilot pack for Paperclip, GitHub PRs, graph ingestion, alerting, canary, and rollback.
