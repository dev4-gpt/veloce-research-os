from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from agent_runner_proof import run  # noqa: E402


def _config(root: Path) -> dict:
    return {
        "generated_json": str(root / "runner.json"),
        "generated_markdown": str(root / "runner.md"),
        "audit_ledger": str(root / "audit.jsonl"),
        "memory_markdown": str(root / "memory.md"),
        "runner_ledger": str(root / "runner.jsonl"),
        "cancel_packet": str(root / "cancel.json"),
        "job_dir": str(root / "jobs"),
        "mode": "dry_run",
        "issue_id": "VEL-test",
        "actor": "test",
        "live_enable_env": "VELOCE_AGENT_RUNNER_LIVE",
        "live_enable_value": "1",
        "live_enabled": False,
        "required_live_env": [],
        "job_id": "v2i-test-runner",
        "capability": "long_running_agent_jobs",
        "lease_owner": "test-runner",
        "budget_minutes": 20,
        "heartbeat_seconds": 60,
        "max_steps": 2,
        "planned_steps": ["step one", "step two", "step three"],
    }


class AgentRunnerProofTest(unittest.TestCase):
    def test_dry_run_writes_bounded_runner_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(config_path, environ={})

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "dry_run_ready")
            self.assertEqual(report["job_result"]["decision"], "written_dry_run")
            self.assertFalse(report["production_mutation_performed"])
            self.assertEqual(
                [event["event"] for event in report["runner_events"]].count("step_planned"),
                2,
            )
            self.assertTrue((root / "jobs/v2i-test-runner.json").exists())
            self.assertTrue((root / "runner.jsonl").exists())
            self.assertTrue((root / "cancel.json").exists())

    def test_live_request_blocks_when_not_live_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(config_path, environ={"VELOCE_AGENT_RUNNER_LIVE": "1"})

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_live_not_enabled")
            self.assertEqual(report["job_result"]["decision"], "blocked_not_written")
            self.assertFalse((root / "jobs/v2i-test-runner.json").exists())

    def test_live_ready_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config["live_enabled"] = True
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            report = run(config_path, environ={"VELOCE_AGENT_RUNNER_LIVE": "1"})

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "live_ready")
            self.assertEqual(report["runner_result"]["decision"], "written_live_ready")
            self.assertFalse(report["production_mutation_performed"])


if __name__ == "__main__":
    unittest.main()
