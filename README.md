# Veloce Research OS

Veloce Research OS is the working knowledge base and execution scaffold for a 30-day AI systems research project.

The first flagship project is **Reliability Policy Matrix for Computer-Use Agents**: a reproducible benchmark scaffold for comparing agent reliability policies across scoped computer-use tasks.

## Structure

```text
docs/
  research-os-v1.md
  artifact-index.md
  setup-log.md
artifacts/
  primary/
  audit/
projects/
  reliability-policy-matrix/
```

## Start Here

1. Read `docs/research-os-v1.md`.
2. Review the primary Paperclip artifacts in `artifacts/primary/`.
3. Build from `projects/reliability-policy-matrix/`.

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
