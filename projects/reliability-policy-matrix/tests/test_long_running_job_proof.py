from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from long_running_job_proof import run  # noqa: E402


def _config(root: Path) -> dict:
    return {
        "generated_json": str(root / "job.json"),
        "generated_markdown": str(root / "job.md"),
        "audit_ledger": str(root / "audit.jsonl"),
        "memory_markdown": str(root / "memory.md"),
        "heartbeat_ledger": str(root / "heartbeat.jsonl"),
        "job_dir": str(root / "jobs"),
        "mode": "dry_run",
        "issue_id": "VEL-test",
        "actor": "test",
        "live_enable_env": "VELOCE_LONG_JOB_LIVE",
        "live_enable_value": "1",
        "live_enabled": False,
        "job_id": "v2c-test-job",
        "capability": "long_running_agent_jobs",
        "lease_owner": "test-controller",
        "budget_minutes": 10,
        "max_attempts": 1,
        "heartbeat_seconds": 60,
        "stale_after_seconds": 180,
        "loop_budget": {"max_steps": 4, "max_runtime_seconds": 600, "max_cost_usd": 0.25},
        "stale_probe": {"enabled": True, "job_id": "v2c-stale-probe", "last_heartbeat_age_seconds": 240},
    }


class LongRunningJobProofTest(unittest.TestCase):
    def test_dry_run_writes_job_heartbeat_audit_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(config_path, environ={})

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "dry_run_ready")
            self.assertEqual(report["job_result"]["decision"], "written_dry_run")
            self.assertEqual(report["heartbeat_result"]["decision"], "written_dry_run")
            self.assertTrue((root / "jobs" / "v2c-test-job.json").exists())
            self.assertTrue((root / "heartbeat.jsonl").exists())
            self.assertTrue((root / "audit.jsonl").exists())
            self.assertIn("Long-Running Job Heartbeat", (root / "memory.md").read_text(encoding="utf-8"))

    def test_stale_probe_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(config_path, environ={})

            self.assertEqual(len(report["stale_jobs"]), 1)
            self.assertEqual(report["stale_jobs"][0]["job_id"], "v2c-stale-probe")

    def test_live_request_blocks_when_not_live_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(json.dumps(_config(root)), encoding="utf-8")

            report = run(config_path, environ={"VELOCE_LONG_JOB_LIVE": "1"})

            self.assertFalse(report["ok"])
            self.assertEqual(report["decision"], "blocked_live_not_enabled")
            self.assertEqual(report["job_packet"]["status"], "blocked")
            self.assertEqual(report["job_result"]["decision"], "blocked_not_written")
            self.assertFalse((root / "jobs" / "v2c-test-job.json").exists())

    def test_live_ready_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = _config(root)
            config["live_enabled"] = True
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            report = run(config_path, environ={"VELOCE_LONG_JOB_LIVE": "1"})

            self.assertTrue(report["ok"])
            self.assertEqual(report["decision"], "live_ready")
            self.assertEqual(report["job_result"]["decision"], "written_live_ready")


if __name__ == "__main__":
    unittest.main()
