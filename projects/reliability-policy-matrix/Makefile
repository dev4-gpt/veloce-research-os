.PHONY: matrix-plan run-sample aggregate-sample week1-plan week1-sample week1-full stack-health security-access-review rollback-drill autonomy-controls autonomy-readiness production-execution production-runner-once production-runner-status production-ai-os-pilot-pack paperclip-credential-discovery-v3-2 paperclip-writeback-v3-2 paperclip-writeback-proof chat-to-pr-proof long-running-job-proof canary-deploy-proof autonomous-rollback-proof paperclip-live-writeback-pilot chat-to-pr-live-pilot canary-deploy-live-pilot agent-runner-proof v2-e-to-i test clean

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

production-runner-once:
	$(PYTHON) scripts/production_job_runner.py --config configs/production_job_runner_v2_1.json --action run-once

production-runner-status:
	$(PYTHON) scripts/production_job_runner.py --config configs/production_job_runner_v2_1.json --action status

production-ai-os-pilot-pack:
	$(PYTHON) scripts/production_ai_os_pilot_pack.py --config configs/production_ai_os_v2_6_v3_1.json

paperclip-credential-discovery-v3-2:
	$(PYTHON) scripts/paperclip_credential_discovery_v3_2.py --config configs/paperclip_credential_discovery_v3_2.json

paperclip-writeback-v3-2:
	$(PYTHON) scripts/paperclip_live_writeback_v3_2.py --config configs/paperclip_writeback_v3_2.json

paperclip-writeback-proof:
	$(PYTHON) scripts/paperclip_writeback_proof.py --config configs/paperclip_writeback_v2_0A.json

chat-to-pr-proof:
	$(PYTHON) scripts/chat_to_pr_proof.py --config configs/chat_to_pr_v2_0B.json

long-running-job-proof:
	$(PYTHON) scripts/long_running_job_proof.py --config configs/long_running_job_v2_0C.json

canary-deploy-proof:
	$(PYTHON) scripts/canary_deploy_proof.py --config configs/canary_deploy_v2_0D.json

autonomous-rollback-proof:
	$(PYTHON) scripts/autonomous_rollback_proof.py --config configs/autonomous_rollback_v2_0E.json

paperclip-live-writeback-pilot:
	$(PYTHON) scripts/paperclip_writeback_proof.py --config configs/paperclip_writeback_v2_0F.json

chat-to-pr-live-pilot:
	$(PYTHON) scripts/chat_to_pr_proof.py --config configs/chat_to_pr_v2_0G.json

canary-deploy-live-pilot:
	$(PYTHON) scripts/canary_deploy_proof.py --config configs/canary_deploy_v2_0H.json

agent-runner-proof:
	$(PYTHON) scripts/agent_runner_proof.py --config configs/agent_runner_v2_0I.json

v2-e-to-i: autonomous-rollback-proof paperclip-live-writeback-pilot chat-to-pr-live-pilot canary-deploy-live-pilot agent-runner-proof production-execution production-runner-once production-ai-os-pilot-pack

test:
	$(PYTHON) -m unittest discover -s tests

clean:
	rm -f artifacts/raw/*.json artifacts/derived/*.csv
