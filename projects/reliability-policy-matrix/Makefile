.PHONY: matrix-plan run-sample aggregate-sample week1-plan week1-sample week1-full stack-health security-access-review rollback-drill autonomy-controls autonomy-readiness production-execution paperclip-writeback-proof test clean

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

stack-health:
	$(PYTHON) scripts/stack_health_monitor.py --config configs/stack_health_v1_7C.json

security-access-review:
	$(PYTHON) scripts/security_access_review.py --config configs/access_review_v1_7D.json

rollback-drill:
	$(PYTHON) scripts/rollback_drill.py --config configs/rollback_drill_v1_7F.json

autonomy-controls:
	$(PYTHON) scripts/autonomy_control_plane.py --config configs/autonomy_controls_v1_8.json

autonomy-readiness:
	$(PYTHON) scripts/autonomy_readiness_gate.py --config configs/autonomy_readiness_v1_8.json

production-execution:
	$(PYTHON) scripts/production_execution_control_plane.py --config configs/production_execution_v2_0.json

paperclip-writeback-proof:
	$(PYTHON) scripts/paperclip_writeback_proof.py --config configs/paperclip_writeback_v2_0A.json

test:
	$(PYTHON) -m unittest discover -s tests

clean:
	rm -f artifacts/raw/*.json artifacts/derived/*.csv
