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
- VEL-124 validation passed externally with `PYTHONPATH=. pytest -q`, producing `3 passed in 0.01s`.
