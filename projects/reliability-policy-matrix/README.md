# Reliability Policy Matrix

Reliability Policy Matrix is a reproducible experiment scaffold for comparing computer-use agent reliability policies.

## Goal

Measure which policy stack produces the best completion/reliability tradeoff on realistic computer-use tasks under fixed action and token budgets.

## Policy Variants

- `P0`: ReAct baseline
- `P1`: ReAct + reflection checkpoint
- `P2`: ReAct + recovery playbook

## Benchmark Slices

- OSWorld subset
- VisualWebArena subset
- ITBench subset

The current repository uses placeholder manifests so the command path works before real benchmark credentials and task definitions are added.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make matrix-plan
make run-sample
make aggregate-sample
```

The default runner mode is `dry-run`. It writes deterministic placeholder
records so the matrix, aggregation, and dashboard plumbing can be tested before
real benchmark credentials exist.

```bash
python3 scripts/run_matrix.py --config configs/matrix.base.yaml --mode dry-run --limit 3
```

Step 17 adds the first adapter path. `adapter-stub` validates that benchmark
manifests can be loaded through an adapter interface without launching the real
OSWorld, VisualWebArena, or ITBench runtimes yet.

```bash
python3 scripts/run_matrix.py --config configs/matrix.week1_day1_3.yaml --mode adapter-stub --limit 1
```

## Week 1 Day 1-3 Commands

```bash
make week1-plan
make week1-sample
make week1-full
```

## V1.7C Stack Health Monitor

Run from the VPS with `MCPO_API_KEY` loaded:

```bash
cd /root/ai-agency
set -a
source .env
set +a

cd /root/veloce-research-os/projects/reliability-policy-matrix
make stack-health
```

The monitor writes:

```text
artifacts/derived/stack_health_v1_7C.json
```

## V1.7D Security Access Review

Run from the repository project directory:

```bash
make security-access-review
```

The review writes:

```text
artifacts/derived/security_access_review_v1_7D.json
artifacts/derived/security_access_review_v1_7D.md
```

## V1.7F Rollback Drill

Run on the VPS after at least one backup/restore-test path exists:

```bash
make rollback-drill
make stack-health
```

The drill writes:

```text
artifacts/derived/rollback_drill_v1_7F.json
```

## V1.8 Autonomy Readiness Gate

Run before enabling unattended production writes:

```bash
make autonomy-controls
make autonomy-readiness
```

The gate intentionally fails closed until v1.8 controls pass. It writes:

```text
artifacts/derived/autonomy_readiness_v1_8.json
artifacts/derived/autonomy_readiness_v1_8.md
```

## V2.0 Production Execution Control Plane

Run before enabling live Paperclip writeback, chat-to-PR, canary deploy, rollback, or long-running jobs:

```bash
make production-execution
```

The control plane writes dry-run job packets and an audit ledger, then blocks live execution unless `VELOCE_V2_LIVE=1`, the capability is explicitly `live_enabled`, scoped env vars are present, and the kill switch is absent.

```text
artifacts/derived/production_execution_v2_0.json
artifacts/derived/production_execution_v2_0.md
artifacts/derived/production_execution_audit_v2_0.jsonl
artifacts/derived/v2_jobs/
```

## Outputs

Generated outputs are written under:

```text
artifacts/raw/
artifacts/derived/
artifacts/figures/
```

Generated artifacts are ignored by git except for `.gitkeep` files.

## Reproducibility Contract

- Keep all experiment configs in versioned YAML.
- Store raw run records separately from derived metrics.
- Capture run ID, benchmark, policy, seed, budget, timestamp, and git SHA.
- Do not commit secrets or provider keys.
- Use placeholder manifests until real benchmark tasks are approved.
