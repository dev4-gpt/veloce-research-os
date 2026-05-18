# VEL-61 Step 09 - 30-Day Execution Plan for Flagship Project

Scope: Convert the Step-08 flagship selection into an execution-ready 30-day plan with day-level actions, clear exit criteria, and a verification cadence.

Flagship project (from Step 08):
- **Reliability Policy Matrix for Computer-Use Agents**

Project objective:
- Deliver a reproducible reliability benchmark package comparing `P0` (ReAct), `P1` (ReAct+reflection), and `P2` (ReAct+recovery) on scoped subsets of OSWorld, VisualWebArena, and ITBench.

## 1) Operating Constraints and Ground Rules

- Timebox: 30 calendar days.
- Scope lock for this cycle:
  - 3 policy variants only (`P0`, `P1`, `P2`).
  - Benchmark subsets only (no full benchmark expansion).
  - Fixed action/token budgets per task class.
- Reproducibility requirements:
  - pinned dependencies,
  - explicit seeds,
  - immutable raw logs,
  - run IDs tied to git SHA.

## 2) Roles and Ownership

- Project lead / integrator:
  - Owns milestones, merge decisions, risk control, and final release.
- Evaluation engineer:
  - Owns adapters, runners, metrics pipeline, and experiment orchestration.
- Policy engineer:
  - Owns `P1` and `P2` reliability policy implementations.
- QA/repro reviewer:
  - Owns clean-environment rerun validation and doc fidelity checks.

Note: one person can hold multiple roles if team size is small; role ownership still applies.

## 3) Milestones and Gates

- M1 (Day 7): Deterministic baseline pipeline complete.
- M2 (Day 14): All three policies runnable from one matrix config.
- M3 (Day 21): Full matrix executed with 3-seed reruns and aggregate tables.
- M4 (Day 30): Reproducibility pass + report + demo package published.

Go/no-go gates:
- Gate A (Day 7): baseline reproducibility on repeat run.
- Gate B (Day 14): policy parity and metric output consistency.
- Gate C (Day 21): data completeness across all configured conditions.
- Gate D (Day 30): independent clean rerun succeeds from docs.

## 4) Day-by-Day Execution Plan

### Days 1-3: Foundation

Day 1:
- Initialize repository scaffold (`src`, `configs`, `scripts`, `reports`, `docs`).
- Set up dependency management and lockfile.
- Add CI for lint + unit smoke checks.
- Output:
  - bootstrapped repo and passing CI on baseline skeleton.

Day 2:
- Implement run logging schema (`run_id`, `seed`, `git_sha`, policy, benchmark, budget, outcome).
- Add deterministic seed utility and run metadata capture.
- Output:
  - first deterministic local smoke run with structured logs.

Day 3:
- Draft benchmark subset manifests for OSWorld/VisualWebArena/ITBench.
- Add manifest validation script.
- Output:
  - validated manifests committed with documented selection rationale.

### Days 4-7: Baseline Completion (M1)

Day 4:
- Implement `P0` runner path end-to-end on one benchmark subset.
- Output:
  - successful baseline run artifact.

Day 5:
- Extend `P0` to all three benchmark subsets.
- Add failure taxonomy placeholder labels.
- Output:
  - baseline coverage across all subsets.

Day 6:
- Implement metrics aggregation (`completion_rate`, `success_under_budget`, `critical_failure_rate`, `mean_steps`).
- Output:
  - generated summary table for baseline results.

Day 7:
- Re-run baseline with fixed seeds to confirm determinism envelope.
- Gate A review and milestone signoff.
- Output:
  - M1 signoff note with reproducibility evidence.

### Days 8-11: Reflection Policy (`P1`)

Day 8:
- Implement reflection checkpoint wrapper and config toggles.
- Output:
  - `P1` compiles/runs on smoke subset.

Day 9:
- Add instrumentation for reflection trigger frequency and delta outcomes.
- Output:
  - per-run reflection stats in logs.

Day 10:
- Execute `P1` on all benchmark subsets (single-seed pass).
- Output:
  - first complete `P1` result set.

Day 11:
- Debug parity issues and normalize evaluator interface across `P0`/`P1`.
- Output:
  - stable cross-policy invocation contract.

### Days 12-14: Recovery Policy (`P2`) + Milestone M2

Day 12:
- Implement recovery playbook (retry/replan/escalate heuristic sequence).
- Output:
  - `P2` runner operational on smoke subset.

Day 13:
- Run `P2` on all subsets and collect comparable metrics.
- Output:
  - initial `P2` result set.

Day 14:
- Wire unified `matrix_v1` config for `P0/P1/P2`.
- Gate B review and M2 signoff.
- Output:
  - single-command matrix entrypoint validated.

### Days 15-18: Matrix Runs (pass 1)

Day 15:
- Launch full matrix pass with seed set A.
- Output:
  - condition coverage report.

Day 16:
- Launch seed set B.
- Output:
  - second-seed run logs and interim aggregates.

Day 17:
- Launch seed set C.
- Output:
  - third-seed run logs and completeness check.

Day 18:
- Resolve failed runs; rerun only incomplete/invalid conditions.
- Output:
  - clean condition matrix with no missing cells.

### Days 19-21: Analysis + Milestone M3

Day 19:
- Compute aggregate metrics and variance bands.
- Output:
  - policy-by-benchmark comparison tables.

Day 20:
- Build failure taxonomy breakdown and representative failure cases.
- Output:
  - failure distribution summary and examples.

Day 21:
- Gate C review: verify all planned conditions present and reproducible metadata complete.
- Output:
  - M3 signoff with data completeness checklist.

### Days 22-26: Reproducibility and Report Drafting

Day 22:
- Fresh-environment setup run from docs by QA/repro reviewer.
- Output:
  - repro test log with environment details.

Day 23:
- Fix reproducibility/documentation defects from Day 22.
- Output:
  - reproducibility delta patch.

Day 24:
- Draft report methods and experiment setup sections.
- Output:
  - report draft v1 (methods).

Day 25:
- Draft results and limitations sections with figures.
- Output:
  - report draft v2 (results + threats to validity).

Day 26:
- Internal technical review of claims vs evidence.
- Output:
  - review checklist with resolved edits.

### Days 27-30: Release Packaging + Milestone M4

Day 27:
- Finalize README quickstart and reproducibility guide.
- Output:
  - external-user-oriented quickstart path.

Day 28:
- Prepare demo notebook/script for one complete replay path.
- Output:
  - replay demo validated.

Day 29:
- Run release candidate validation:
  - one-command matrix run (scoped),
  - artifact generation,
  - report render.
- Output:
  - release candidate checklist passed.

Day 30:
- Gate D review and publication package freeze.
- Output:
  - M4 signoff and final release bundle.

## 5) Weekly Review Cadence

- Weekly review checkpoints: Day 7, 14, 21, 30.
- Required review artifacts each checkpoint:
  - progress vs planned milestone,
  - risks/issues and mitigation actions,
  - acceptance-gate status,
  - any approved scope changes.

## 6) Risk Register with Trigger Conditions

Risk 1: Adapter instability delays runs.
- Trigger: >20% tasks fail for infra reasons on any day.
- Action: freeze new policy work; prioritize adapter hardening for 24-48h.

Risk 2: Runtime cost/time overrun.
- Trigger: projected matrix completion slips >2 days.
- Action: reduce per-subset task count while preserving cross-benchmark coverage.

Risk 3: Policy deltas are statistically noisy.
- Trigger: confidence intervals overlap heavily across all metrics.
- Action: prioritize failure-taxonomy insights and conservative claims.

Risk 4: Reproducibility failure late in cycle.
- Trigger: clean rerun cannot reproduce key table/plot.
- Action: block publication until repro defect is fixed and rerun passes.

## 7) Acceptance Criteria for Step 09 Completion

This Step-09 planning deliverable is complete when:
- A full day-level 30-day execution plan exists.
- Milestones, gates, and ownership are explicit.
- Outputs are defined for each phase.
- Risk triggers and mitigation actions are documented.
- Plan is directly executable without additional decomposition.

## 8) Disposition

Status recommendation: `done`
Reason: The requested Step-09 deliverable (concrete 30-day execution plan for the chosen flagship project) is now fully specified with daily actions, milestones, gates, owners, and completion criteria.
