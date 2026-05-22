from pathlib import Path
import json
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from production_job_runner import (  # noqa: E402
    approve_job,
    audit_tail,
    cancel_job,
    enqueue_job,
    run_once,
    status,
    validate_packet,
)


def _config(root: Path) -> dict:
    return {
        "generated_json": str(root / "runner.json"),
        "audit_ledger": str(root / "audit.jsonl"),
        "runner_ledger": str(root / "runner.jsonl"),
        "job_dir": str(root / "jobs"),
        "state_dir": str(root / "states"),
        "memory_dir": str(root / "memory"),
        "mode": "dry_run",
        "issue_id": "VEL-test",
        "lease_owner": "test-runner",
        "lease_seconds": 120,
        "stale_after_seconds": 1,
        "simulate_canary_failure": False,
    }


class ProductionJobRunnerTest(unittest.TestCase):
    def test_enqueue_approve_run_once_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config_path = root / "runner_config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            enqueue = enqueue_job(
                config,
                {
                    "id": "job-1",
                    "capability": "paperclip_writeback",
                    "budget_minutes": 5,
                    "max_attempts": 1,
                    "heartbeat_seconds": 60,
                },
            )
            self.assertTrue(enqueue["ok"])
            self.assertEqual(enqueue["decision"], "queued_dry_run")

            approve = approve_job(config, "job-1", "Aryaman")
            self.assertTrue(approve["ok"])
            self.assertEqual(approve["decision"], "approved_for_live_candidate")

            report = run_once(config_path)
            self.assertTrue(report["ok"])
            self.assertEqual(report["states"][0]["state"], "completed")
            self.assertTrue((root / "memory").exists())

            tail = audit_tail(config, limit=10)
            self.assertTrue(tail["ok"])
            transitions = {item.get("transition") for item in tail["records"]}
            self.assertIn("completed", transitions)

    def test_cancel_marks_terminal_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = _config(Path(tmp))
            enqueue_job(config, {"id": "job-cancel", "capability": "chat_to_pr"})

            result = cancel_job(config, "job-cancel", "operator changed plan")

            self.assertTrue(result["ok"])
            self.assertEqual(result["decision"], "cancelled")
            one = status(config, "job-cancel")
            self.assertEqual(one["state"]["state"], "cancelled")

    def test_rejects_raw_command_and_secret_like_payloads(self) -> None:
        command_packet = {
            "id": "bad",
            "capability": "chat_to_pr",
            "status": "queued_dry_run",
            "policy_decision": "dry_run_ready",
            "budget_minutes": 5,
            "max_attempts": 1,
            "heartbeat_seconds": 60,
            "input_hash": "abc",
            "secret_free": True,
            "command": "docker restart prod",
        }
        secret_packet = dict(command_packet)
        secret_packet.pop("command")
        secret_packet["notes"] = "Bearer abcdefghijklmnopqrstuvwxyz"

        self.assertTrue(any("forbidden packet keys" in item for item in validate_packet(command_packet)))
        self.assertTrue(any("secret-like content" in item for item in validate_packet(secret_packet)))

    def test_stale_lease_is_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config_path = root / "runner_config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            enqueue_job(config, {"id": "job-stale", "capability": "long_running_agent_jobs"})
            state_path = root / "states" / "job-stale.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["lease_owner"] = "old-runner"
            state["lease_expires_at"] = 1
            state_path.write_text(json.dumps(state), encoding="utf-8")

            report = run_once(config_path, "job-stale")

            self.assertTrue(report["ok"])
            self.assertEqual(report["states"][0]["state"], "completed")
            ledger = (root / "runner.jsonl").read_text(encoding="utf-8")
            self.assertIn("stale_lease_recovered", ledger)

    def test_canary_failure_moves_to_rollback_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config["simulate_canary_failure"] = True
            config_path = root / "runner_config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            enqueue_job(config, {"id": "job-canary", "capability": "chat_to_canary_deploy"})

            report = run_once(config_path, "job-canary")

            self.assertEqual(report["states"][0]["state"], "rollback_required")


if __name__ == "__main__":
    unittest.main()
