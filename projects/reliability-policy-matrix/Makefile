.PHONY: matrix-plan run-sample aggregate-sample week1-plan week1-sample week1-full test clean

PYTHON ?= python3

matrix-plan:
	$(PYTHON) scripts/matrix_plan.py --config configs/matrix.base.yaml

run-sample:
	$(PYTHON) scripts/run_matrix.py --config configs/matrix.base.yaml --limit 3

aggregate-sample:
	$(PYTHON) scripts/aggregate_metrics.py --raw-dir artifacts/raw --out artifacts/derived/summary.csv

week1-plan:
	$(PYTHON) scripts/matrix_plan.py --config configs/matrix.week1_day1_3.yaml

week1-sample:
	$(PYTHON) scripts/run_matrix.py --config configs/matrix.week1_day1_3.yaml --limit 3
	$(PYTHON) scripts/aggregate_metrics.py --raw-dir artifacts/raw --out artifacts/derived/week1_summary.csv

week1-full:
	sh scripts/week1_day1_3.sh

test:
	$(PYTHON) -m unittest discover -s tests

clean:
	rm -f artifacts/raw/*.json artifacts/derived/*.csv
