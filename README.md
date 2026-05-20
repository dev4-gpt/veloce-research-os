# Veloce Research OS

Veloce Research OS is a self-hosted research and agent-operations stack for building reproducible AI systems work.

It combines a research repository, a Paperclip task ledger, Open WebUI as the operator cockpit, Hermes for agent behavior and memory experiments, MCPO for safe tool exposure, and a gated Ruflo sandbox for planning-only orchestration experiments.

The first flagship research project is **Reliability Policy Matrix for Computer-Use Agents**: a reproducible benchmark scaffold for comparing agent reliability policies across scoped computer-use tasks.

## Current Pipeline

```text
Operator
  -> Open WebUI
    -> native Open WebUI tools
      -> MCPO proxy
        -> allowlisted MCP-derived HTTP tools

Operator / Agents
  -> Paperclip
    -> durable issues, dispositions, comments, artifacts
    -> Hermes HTTP shim when memory or Hermes agent behavior is needed

GitHub
  -> source of truth for code, docs, deploy manifests, and reproducible runbooks

VPS
  -> runtime proof for Docker services, MCPO tools, Hermes, Paperclip, Open WebUI

Obsidian
  -> human-readable research notebook and exported Paperclip evidence

Ruflo
  -> isolated planning-only sandbox until production safety gates are met
```

The production rule is intentionally conservative: Open WebUI can call safe tools, Paperclip tracks work, GitHub/VPS prove changes, and Ruflo remains sandboxed until it can be trusted not to mutate production state.

## Structure

```text
docs/
  research-os-v1.md
  artifact-index.md
  setup-log.md
  status-check-tool.md
  mcpo-stack-status-tool.md
  mcpo-repo-status-tool.md
  mcpo-ruflo-status-tool.md
  mcpo-ruflo-plan-tool.md
  ruflo-sandbox-evaluation.md
  pipeline-setup.md
  v1.4-hermes-mcpo-ruflo-plan.md
  v1.5-mcpo-ruflo-orchestration.md
  v1.6-ruflo-planning-closeout.md
artifacts/
  primary/
  audit/
deploy/
  ai-agency/
projects/
  reliability-policy-matrix/
tools/
  openwebui/
  paperclip/
  status-check-server/
  mcpo/
  mcpo-openwebui-proxy/
```

## Start Here

1. Read `docs/research-os-v1.md`.
2. Review the primary Paperclip artifacts in `artifacts/primary/`.
3. Build from `projects/reliability-policy-matrix/`.
4. For service integration, read `docs/v1.2-integration-plan.md`.
5. For the first Open WebUI tool, read `docs/status-check-tool.md`.
6. For the v1.3 Paperclip-to-Hermes bridge, read `docs/paperclip-hermes-http-agent.md`.
7. For Hermes token control plus MCPO/Ruflo expansion, read `docs/v1.4-hermes-mcpo-ruflo-plan.md`.
8. For the next MCPO and Ruflo orchestration path, read `docs/v1.5-mcpo-ruflo-orchestration.md`.
9. For the first read-only MCPO status expansion, read `docs/mcpo-stack-status-tool.md`.
10. For the read-only repository status tool, read `docs/mcpo-repo-status-tool.md`.
11. For the Ruflo planning-only sandbox gate, read `docs/ruflo-sandbox-evaluation.md`.
12. For the complete deployed pipeline and reproduction commands, read `docs/pipeline-setup.md`.
13. For the v1.6 Ruflo planning closeout, read `docs/v1.6-ruflo-planning-closeout.md`.
14. For the first read-only Ruflo cockpit integration, read `docs/mcpo-ruflo-status-tool.md`.
15. For the first Paperclip-shaped Ruflo planning bridge, read `docs/mcpo-ruflo-plan-tool.md`.
16. For the approval-gated Paperclip execution handoff, read `docs/mcpo-ruflo-execution-packet-tool.md`.
17. For the first end-to-end OpenWebUI/MCPO/Ruflo/Paperclip demo proof, read `docs/v1.6-end-to-end-ruflo-paperclip-demo.md`.
18. For the production-readiness gate and next Paperclip tasks, read `docs/v1.7-production-readiness-plan.md`.
19. For the VEL-129 Paperclip runtime blocker workaround, read `docs/v1.7A-external-validation-unblock.md`.
20. For the VEL-130 backup and restore runbook, read `docs/v1.7B-backup-restore-runbook.md`.
21. For the VEL-132 monitoring and alerting runbook, read `docs/v1.7C-monitoring-alerting-runbook.md`.
22. For the VEL-134 security and access review, read `docs/v1.7D-security-access-review.md`.
23. For the VEL-142 rollback drill runbook, read `docs/v1.7F-rollback-drill-runbook.md`.
24. For the unattended autonomous production plan, read `docs/v1.8-unattended-autonomy-plan.md`.
25. For the production-level autonomy roadmap, read `docs/v1.8-production-level-next-steps.md`.
26. For the v1.8C-J autonomy control closeout, read `docs/v1.8C-J-autonomy-control-closeout.md`.
27. For the full-capability agentic product roadmap, read `docs/v1.9-full-capability-agentic-product-plan.md`.
28. For the v1.9A-C OpenWebUI/Hermes/Ruflo closeout, read `docs/v1.9A-C-openwebui-hermes-ruflo-closeout.md`.
29. For a public-safe preview page, deploy `showcase/` to Vercel or Netlify.

## Flagship Project

```text
Project: Reliability Policy Matrix for Computer-Use Agents
Repo folder: projects/reliability-policy-matrix
Goal: compare P0/P1/P2 reliability policies under fixed action and token budgets.
```

Initial policy variants:

- `P0`: ReAct baseline
- `P1`: ReAct + reflection checkpoint
- `P2`: ReAct + recovery playbook

Initial benchmark slices:

- OSWorld subset
- VisualWebArena subset
- ITBench subset

## Quickstart

```bash
cd projects/reliability-policy-matrix
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make matrix-plan
make run-sample
make aggregate-sample
```

## Current Status

Planning artifacts are complete and synced from Paperclip/Obsidian. The project scaffold is intentionally minimal and runnable; real benchmark adapters are the next implementation layer.

For the deployed service flow, v1.1 verifies Paperclip, Open WebUI, Hermes standalone, Hermes memory, GitHub, VPS, and Obsidian. V1.2 adds the Open WebUI status tool. V1.3 verifies the Paperclip-to-Hermes HTTP wrapper without relying on the broken local `hermes` command. V1.4 verifies MCPO through a safe time tool. V1.5 expands MCPO with read-only stack and repo tools. V1.6 adds a planning-only Ruflo bridge design and validates the first sandbox bridge test set without enabling Ruflo production execution.

## Operational Status

- Paperclip remains the task ledger and disposition system.
- Open WebUI is the operator cockpit.
- MCPO tools are the safe bridge from chat to explicit HTTP tool endpoints.
- Hermes is available for memory and agent behavior experiments, but not for tiny exact-output acceptance tests.
- Ruflo is installed and initialized only in `/opt/veloce-ruflo-sandbox` through a Node 20 container path, with daemon, swarm, memory, hooks, autopilot, Claude MCP, and Codex MCP disabled for production safety.
- `ruflo_status` is implemented as the first read-only MCPO/OpenWebUI Ruflo integration path.
- `ruflo_plan` is implemented as the first Paperclip-shaped planning-only bridge.
- `ruflo_execution_packet` is implemented as the approval-gated Paperclip handoff for executing approved work through Codex/GitHub/VPS without enabling Ruflo runtime execution.
- V1.6 end-to-end proof is recorded for OpenWebUI -> MCPO -> Ruflo execution packet -> Paperclip handoff.
- V1.7 production-readiness work is sufficient for controlled operator workflows after secret rotation; the stack is not unattended production ready.
- V1.8 defines the unattended autonomy gate and starts with `make autonomy-readiness`.
- VEL-124 validation passed externally with `PYTHONPATH=. pytest -q`, producing `3 passed in 0.01s`.
