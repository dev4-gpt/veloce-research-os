# Veloce Research OS

Veloce Research OS is the working knowledge base and execution scaffold for a 30-day AI systems research project.

The first flagship project is **Reliability Policy Matrix for Computer-Use Agents**: a reproducible benchmark scaffold for comparing agent reliability policies across scoped computer-use tasks.

## Structure

```text
docs/
  research-os-v1.md
  artifact-index.md
  setup-log.md
  status-check-tool.md
  mcpo-stack-status-tool.md
  v1.4-hermes-mcpo-ruflo-plan.md
  v1.5-mcpo-ruflo-orchestration.md
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

For the deployed service flow, v1.1 verifies Paperclip, Open WebUI, Hermes standalone, Hermes memory, GitHub, VPS, and Obsidian. V1.2 adds the Open WebUI status tool. V1.3 verifies the Paperclip-to-Hermes HTTP wrapper without relying on the broken local `hermes` command. V1.4 verifies MCPO through a safe time tool. V1.5 expands MCPO with read-only tools and evaluates Ruflo only as an isolated orchestration sandbox.
