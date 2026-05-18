# VEL-68 Step 12 - Technical Repo Scaffold

Date: 2026-05-18 (UTC)
Status: Complete

## Objective
Create a concrete, buildable repository scaffold for the Reliability Policy Matrix project so experiments can start with reproducible structure and minimal bootstrap friction.

## 1) Proposed Repository Name
`reliability-policy-matrix`

## 2) Repository Purpose
Provide a reproducible experiment framework to compare computer-use agent policy variants (`P0`, `P1`, `P2`) across scoped benchmark subsets with fixed seeds and auditable artifacts.

## Delivered Artifact
- `reliability-policy-matrix/` repository scaffold with runnable skeleton.

## 3) Folder Structure
- Project metadata and install path:
  - `pyproject.toml`
  - `README.md`
  - `.gitignore`
  - `.env.example`
- Experiment configuration:
  - `configs/matrix.base.yaml`
  - `configs/policies/*.yaml`
  - `configs/benchmarks/*.yaml`
- Benchmark subset manifests:
  - `manifests/*.jsonl` placeholders
- Core package:
  - `src/rpmatrix/__init__.py`
  - `src/rpmatrix/config.py`
- Script entrypoints:
  - `scripts/matrix_plan.py`
  - `scripts/run_matrix.py`
  - `scripts/aggregate_metrics.py`
- Validation and workflow:
  - `tests/test_config.py`
  - `Makefile`
- Artifact storage layout:
  - `artifacts/raw/`
  - `artifacts/derived/`
  - `artifacts/figures/`

## 4) README Outline
- Project overview and goals.
- Policy/benchmark matrix scope.
- Setup and quickstart instructions.
- Reproducibility contract.
- MVP commands (`matrix-plan`, `run-sample`, `aggregate-sample`).
- Output artifact conventions.

## 5) Experiment Plan File Outline
- File: `configs/matrix.base.yaml`
- Sections:
  - `name`
  - `benchmarks` list
  - `policies` list
  - `seeds` list
  - `budget` (`max_steps`, `max_tokens`)
  - `output_dir`

## 6) Baseline Implementation Plan
- Build minimal config loader and matrix planner.
- Implement placeholder matrix runner that emits per-condition JSON outputs.
- Implement metrics aggregator to CSV summaries.
- Add minimal test for config loading.
- Keep interfaces stable so real benchmark runners can replace placeholders in Step 13+.

## 7) Evaluation Script Plan
- `scripts/matrix_plan.py`: expand and print matrix conditions.
- `scripts/run_matrix.py`: execute (currently placeholder) and emit run metadata per condition.
- `scripts/aggregate_metrics.py`: read raw JSON records and write derived CSV summaries.

## 8) Data Handling Notes
- Use only scoped subset manifests (`manifests/*.jsonl`) with placeholder task IDs until real subsets are approved.
- Store immutable per-run raw records under `artifacts/raw/`.
- Store derived aggregates under `artifacts/derived/`.
- Keep generated artifacts out of git except `.gitkeep` markers.
- Do not assume unavailable datasets or compute; manifests are explicit and swappable.

## Reproducibility Features Embedded
- Explicit policy x benchmark x seed matrix config.
- Fixed seed list in base config (`13,17,23`).
- Run metadata output includes timestamp, benchmark, policy, seed, git SHA.
- Separation of raw run outputs and derived summaries.

## 9) Reproducibility Checklist
- [x] Pinned dependency specification in `pyproject.toml`.
- [x] Fixed seed list captured in config.
- [x] Policy and benchmark conditions encoded in versioned YAML.
- [x] Run metadata includes git SHA and timestamp.
- [x] Raw and derived outputs separated by directory.
- [x] Deterministic matrix expansion script exists.
- [x] Minimal test included for config-path sanity.
- [x] Setup instructions documented in README.
- [x] Environment variable template included (`.env.example`).
- [x] Artifact gitignore policy defined.

## 10) First 10 GitHub Issues to Create
1. Replace placeholder runner with real OSWorld adapter.
2. Add VisualWebArena adapter with standardized task interface.
3. Add ITBench adapter with subset manifest validation.
4. Implement policy plugin interface (`P0`, `P1`, `P2`) with runtime hooks.
5. Add seed-controlled deterministic execution harness.
6. Add failure taxonomy schema and labeler for run outputs.
7. Add metrics module for completion, budget success, critical failure, and step stats.
8. Add notebook template to generate first reproducible figures from artifacts.
9. Add CI workflow for lint + tests + sample matrix smoke run.
10. Add run manifest + config hashing for exact reproducibility provenance.

## Quickstart (from repo root)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make matrix-plan
make run-sample
make aggregate-sample
```

## Acceptance Check
Step 12 requested a technical repository scaffold. This deliverable provides a concrete, executable structure with initial scripts and reproducibility-first conventions, ready for Step 13 implementation work.
