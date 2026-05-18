# VEL-59 Step 08 - First 30-Day Flagship Project Selection

Scope: Choose one flagship 30-day project from Step 07 and convert it into a concrete, reproducible build plan with measurable outputs.

Selected flagship project:
- **Reliability Policy Matrix for Computer-Use Agents**

Why this is first:
- Highest Step-07 score (19/20) on feasibility + evidence value.
- Strong fit with technical-builder mandate: repo, benchmark harness, experiment matrix, reproducible runs, and publishable artifacts.
- Delivers visible outputs in 30 days without requiring frontier-scale compute.

## 1) Project Definition

Working title:
- `reliable-cu-agent-matrix`

Core question:
- Which reliability policy stack produces the best completion/reliability tradeoff on realistic computer-use tasks under fixed action and token budgets?

Initial benchmark slice (30-day scope):
- OSWorld (subset)
- VisualWebArena (subset)
- ITBench (subset)

Initial policy variants:
- `P0`: ReAct baseline
- `P1`: ReAct + reflection checkpoint
- `P2`: ReAct + recovery playbook

Primary measurable outcomes:
- Task completion rate (%)
- Success-under-budget rate (%)
- Critical failure rate (%)
- Mean steps-to-completion
- Re-run variance across 3 seeded reruns

## 2) Build Artifacts (End of Day 30)

1. Public GitHub repository with runnable experiment pipeline.
2. Reproducible environment (`uv.lock` or `poetry.lock`, pinned versions, seed control).
3. Benchmark task manifests (small, documented subset for each environment).
4. Policy runner + ablation config system.
5. Results package:
- CSV/Parquet run logs
- Aggregated metrics tables
- Plots and failure-taxonomy summary
6. Technical report (`report.md` + PDF export) with method/results/threats-to-validity.
7. Demo notebook/script showing one end-to-end experiment replay.

## 3) Proposed Repository Layout

```text
reliable-cu-agent-matrix/
  README.md
  LICENSE
  pyproject.toml
  uv.lock
  .env.example
  configs/
    benchmarks/
      osworld_subset.yaml
      visualwebarena_subset.yaml
      itbench_subset.yaml
    policies/
      react.yaml
      react_reflect.yaml
      react_recover.yaml
    experiments/
      matrix_v1.yaml
  src/
    agents/
      react_agent.py
      reflect_wrapper.py
      recover_wrapper.py
    evaluators/
      runner.py
      metrics.py
      failure_taxonomy.py
    integrations/
      osworld_adapter.py
      visualwebarena_adapter.py
      itbench_adapter.py
    utils/
      logging.py
      seeds.py
      replay.py
  scripts/
    run_matrix.sh
    aggregate_results.py
    render_report.py
  notebooks/
    01_reliability_matrix_demo.ipynb
  data/
    manifests/
    raw/
    processed/
  reports/
    report.md
    figures/
  docs/
    reproducibility.md
    benchmark_scope.md
```

## 4) 30-Day Execution Plan

Week 1 (Days 1-7): Scaffolding + Deterministic Baseline
- Initialize repo, packaging, lockfile, CI lint/test pipeline.
- Implement adapters for benchmark subset loading.
- Implement `P0` baseline with deterministic seeds/log schema.
- Exit criteria:
- 10+ baseline tasks run end-to-end with reproducible logs.

Week 2 (Days 8-14): Reliability Policies + Instrumentation
- Add `P1` reflection checkpoint policy.
- Add `P2` recovery policy (retry/replan/escalate heuristics).
- Add taxonomy labeling hooks for failures.
- Exit criteria:
- Three policies runnable from one matrix config; metrics generated automatically.

Week 3 (Days 15-21): Matrix Runs + Ablations
- Execute matrix across benchmark subsets with fixed budget caps.
- Run minimum 3 seeded reruns per condition.
- Produce aggregate comparison tables and confidence intervals.
- Exit criteria:
- Complete results table for all policy x benchmark conditions.

Week 4 (Days 22-30): Hardening + Publication Pack
- Reproducibility pass from clean environment.
- Write report and limitations section.
- Finalize demo notebook + README quickstart.
- Exit criteria:
- External user can reproduce at least one full matrix experiment from docs.

## 5) Success Metrics and Acceptance Thresholds

Minimum success thresholds for Step-08 flagship completion:
- `>= 1` reliability policy beats `P0` baseline by `>= 8%` relative completion rate on at least one benchmark subset.
- `>= 90%` of reruns finish without infra/runtime crash.
- Repro check passes from clean clone on a second machine/session using documented steps.
- Report includes:
- exact benchmark subset definition,
- full config references,
- known limitations and failure cases.

## 6) Reproducibility Contract

- Pin all dependencies and model/provider versions in config.
- Use explicit random seeds and store them with each run artifact.
- Keep raw run logs immutable; write derived tables to a separate folder.
- Version each experiment with run ID + git SHA.
- Provide one-command replay for a named run ID.

## 7) Risks and Mitigations

Risk 1: Benchmark setup overhead is too high.
- Mitigation: start with curated small subsets and adapter interfaces; defer full benchmark coverage.

Risk 2: Policy effects are noisy.
- Mitigation: require multi-seed runs and report variance, not single-run claims.

Risk 3: Provider/API instability.
- Mitigation: add retry/backoff + provider abstraction and cache intermediate observations.

Risk 4: Scope creep.
- Mitigation: freeze to 3 policy variants and fixed benchmark subset in first 30 days.

## 8) Immediate Next Build Actions (first 48 hours)

1. Create repo scaffold and deterministic run logger.
2. Define benchmark subset manifests for OSWorld/VisualWebArena/ITBench.
3. Implement `P0` baseline runner and smoke-test on 3 tasks each.
4. Open project board with 4 week-milestone issues mapped to the plan above.

## 9) Disposition

Status recommendation: `done`
Reason: Step 08 requires choosing the first 30-day flagship project; selection is finalized and converted into a concrete reproducible execution blueprint with measurable acceptance criteria.
