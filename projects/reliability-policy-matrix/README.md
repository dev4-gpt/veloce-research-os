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

## V2.6-V3.1 Production AI OS Pilot Pack

Run the next production AI OS completion pack in dry-run mode:

```bash
make production-ai-os-pilot-pack
```

The pack evaluates Paperclip live writeback, chat-to-PR, graph memory ingestion, alert webhook delivery, canary protected deploy, and autonomous rollback as separate gated stages. The committed config remains dry-run safe. A stage can only move toward live action when the global live gate, the stage live gate, `live_enabled=true` in a local config copy, and scoped required env vars are all present.

Outputs:

```text
artifacts/derived/production_ai_os_v2_6_v3_1.json
artifacts/derived/production_ai_os_v2_6_v3_1.md
artifacts/derived/production_ai_os_v2_6_v3_1_audit.jsonl
artifacts/derived/production_ai_os_v2_6_v3_1_memory.md
```

## V3.2 Paperclip Live Writeback

Run read-only Paperclip credential and API-route discovery first:

```bash
make paperclip-credential-discovery-v3-2
```

The discovery report probes likely issue API routes and records whether the Paperclip base URL and automation-token env vars are present without printing secret values. It also prints read-only VPS inspection commands for the Paperclip container. It does not create tokens or mutate Paperclip.

Run the V3.2 wrapper in dry-run mode:

```bash
make paperclip-writeback-v3-2
```

The wrapper locks the first live target to `VEL-v2.0F-PILOT`, creates local untracked wrapper/effective configs under `artifacts/derived/`, adds a V3.2 idempotency marker, records a trace id, and emits a rollback packet for partial failure. Live writeback remains blocked unless `VELOCE_PRODUCTION_AI_OS_LIVE=1`, `VELOCE_PAPERCLIP_WRITEBACK_LIVE=1`, scoped Paperclip env vars, and `live_enabled=true` in a local config copy are all present. If Paperclip does not expose a native scoped token path, add that path before live writeback; do not use a browser session cookie or direct database write as the production automation credential.

After the dry-run has created the local config, the live command is:

```bash
VELOCE_PRODUCTION_AI_OS_LIVE=1 \
VELOCE_PAPERCLIP_WRITEBACK_LIVE=1 \
python3 scripts/paperclip_live_writeback_v3_2.py \
  --config artifacts/derived/paperclip_writeback_v3_2_live.local.json
```

## V2.0A Paperclip Scoped Writeback Proof

Run the scoped Paperclip writeback proof in dry-run mode:

```bash
make paperclip-writeback-proof
```

The proof prepares exactly one Paperclip issue comment and one disposition update. It remains dry-run by default. A live write is blocked unless all of these are true:

- `VELOCE_PAPERCLIP_WRITEBACK_LIVE=1`
- `live_enabled` is explicitly set to `true` in a local config copy
- `PAPERCLIP_BASE_URL` and `PAPERCLIP_AUTOMATION_TOKEN` are present
- the configured endpoint templates match the deployed Paperclip API

Outputs:

```text
artifacts/derived/paperclip_writeback_v2_0A.json
artifacts/derived/paperclip_writeback_v2_0A.md
artifacts/derived/paperclip_writeback_audit_v2_0A.jsonl
artifacts/derived/paperclip_writeback_memory_v2_0A.md
```

## V2.0B Chat-to-PR Proof

Run the chat-to-PR proof in dry-run mode:

```bash
make chat-to-pr-proof
```

The proof prepares a generated GitHub branch, one docs-only proof file, and one pull request. It remains dry-run by default. A live PR is blocked unless all of these are true:

- `VELOCE_CHAT_TO_PR_LIVE=1`
- `live_enabled` is explicitly set to `true` in a local config copy
- `GITHUB_TOKEN` and `GITHUB_REPOSITORY` are present
- the proof file path starts with an allowed prefix such as `docs/`

Outputs:

```text
artifacts/derived/chat_to_pr_v2_0B.json
artifacts/derived/chat_to_pr_v2_0B.md
artifacts/derived/chat_to_pr_audit_v2_0B.jsonl
artifacts/derived/chat_to_pr_memory_v2_0B.md
```

## V2.0C Long-Running Job Heartbeat Proof

Run the long-running job heartbeat proof in dry-run mode:

```bash
make long-running-job-proof
```

The proof prepares one resumable job packet, one heartbeat record, and one stale-job detector pass. It remains dry-run by default. Live-ready mode is blocked unless all of these are true:

- `VELOCE_LONG_JOB_LIVE=1`
- `live_enabled` is explicitly set to `true` in a local config copy

Outputs:

```text
artifacts/derived/long_running_job_v2_0C.json
artifacts/derived/long_running_job_v2_0C.md
artifacts/derived/long_running_job_audit_v2_0C.jsonl
artifacts/derived/long_running_job_heartbeat_v2_0C.jsonl
artifacts/derived/long_running_job_memory_v2_0C.md
artifacts/derived/v2C_jobs/
```

## V2.0D Chat-to-Canary Deploy Proof

Run the canary deploy proof in dry-run mode:

```bash
make canary-deploy-proof
```

The proof prepares a no-op canary candidate, pre/post health snapshots, a rollback packet, and an alert packet. It remains dry-run by default. Live-ready mode is blocked unless all of these are true:

- `VELOCE_CANARY_DEPLOY_LIVE=1`
- `live_enabled` is explicitly set to `true` in a local config copy
- `VELOCE_CANARY_APPROVED` is present

V2.0D does not mutate production, even in live-ready mode.

Outputs:

```text
artifacts/derived/canary_deploy_v2_0D.json
artifacts/derived/canary_deploy_v2_0D.md
artifacts/derived/canary_deploy_audit_v2_0D.jsonl
artifacts/derived/canary_deploy_memory_v2_0D.md
artifacts/derived/canary_deploy_packet_v2_0D.json
artifacts/derived/canary_rollback_packet_v2_0D.json
artifacts/derived/canary_alert_packet_v2_0D.json
```

## V2.0E-I Production Pilot Pack

Run the remaining V2.0 proof/pilot pack in dry-run mode:

```bash
make v2-e-to-i
```

The pack adds:

- `make autonomous-rollback-proof`
- `make paperclip-live-writeback-pilot`
- `make chat-to-pr-live-pilot`
- `make canary-deploy-live-pilot`
- `make agent-runner-proof`

The committed configs stay dry-run safe. Live-capable pilots are blocked unless their explicit env gate is set, `live_enabled` is changed to `true` in a local config copy, scoped credentials or approvals are present, and the production control plane allows the capability. The rollback and canary pilot scripts still perform no production mutation; they prepare packets, health/verification evidence, alerts, and audit records.

Outputs include:

```text
artifacts/derived/autonomous_rollback_v2_0E.json
artifacts/derived/paperclip_writeback_v2_0F.json
artifacts/derived/chat_to_pr_v2_0G.json
artifacts/derived/canary_deploy_v2_0H.json
artifacts/derived/agent_runner_v2_0I.json
artifacts/derived/v2I_jobs/
```

## V2.1-V2.5 Durable Production Runner

Run the durable execution status and one safe runner pass:

```bash
make production-runner-status
make production-runner-once
```

The runner consumes typed job packets from `artifacts/derived/v2_jobs`, writes state under `artifacts/derived/v2_runner_state`, and mirrors every transition into audit JSONL plus graph-memory markdown. It does not accept raw shell, raw Docker, raw tokens, arbitrary paths, or untyped commands.

Outputs include:

```text
artifacts/derived/production_job_runner_v2_1.json
artifacts/derived/production_job_runner_events_v2_1.jsonl
artifacts/derived/v2_runner_state/
artifacts/derived/graph-memory-events/
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
