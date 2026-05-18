#!/usr/bin/env bash
set -euo pipefail

python3 scripts/matrix_plan.py --config configs/matrix.week1_day1_3.yaml
python3 scripts/run_matrix.py --config configs/matrix.week1_day1_3.yaml
python3 scripts/aggregate_metrics.py --raw-dir artifacts/raw --out artifacts/derived/week1_summary.csv
