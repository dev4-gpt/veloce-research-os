from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any


SECRET_KEYS = {"authorization", "token", "api_key", "password", "secret"}


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    return data


def _checked_at() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _epoch() -> int:
    return int(time.time())


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[redacted]" if any(secret in key.lower() for secret in SECRET_KEYS) else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _env(environ: dict[str, str] | None = None) -> dict[str, str]:
    return environ if environ is not None else os.environ


def _is_live_requested(config: dict[str, Any], environ: dict[str, str] | None = None) -> bool:
    env = _env(environ)
    return env.get(str(config.get("live_enable_env", "VELOCE_LONG_JOB_LIVE"))) == str(
        config.get("live_enable_value", "1")
    )


def _job_packet(config: dict[str, Any], checked_at: str, now_epoch: int, decision: str) -> dict[str, Any]:
    payload = {
        "issue_id": str(config.get("issue_id", "")),
        "job_id": str(config.get("job_id", "")),
        "capability": str(config.get("capability", "long_running_agent_jobs")),
        "budget_minutes": int(config.get("budget_minutes", 10)),
        "max_attempts": int(config.get("max_attempts", 1)),
        "heartbeat_seconds": int(config.get("heartbeat_seconds", 60)),
        "loop_budget": config.get("loop_budget", {}),
    }
    if decision == "dry_run_ready":
        status = "queued_dry_run"
    elif decision == "live_ready":
        status = "queued_live_ready"
    else:
        status = "blocked"
    return {
        "id": payload["job_id"],
        "issue_id": payload["issue_id"],
        "capability": payload["capability"],
        "status": status,
        "policy_decision": decision,
        "budget_minutes": payload["budget_minutes"],
        "max_attempts": payload["max_attempts"],
        "heartbeat_seconds": payload["heartbeat_seconds"],
        "lease_owner": str(config.get("lease_owner", "veloce-production-controller")),
        "created_at": checked_at,
        "created_epoch": now_epoch,
        "input_hash": _digest(payload),
        "secret_free": True,
    }


def _heartbeat(job: dict[str, Any], checked_at: str, now_epoch: int, decision: str) -> dict[str, Any]:
    if decision == "dry_run_ready":
        status = "heartbeat_dry_run"
    elif decision == "live_ready":
        status = "heartbeat_live_ready"
    else:
        status = "heartbeat_blocked"
    return {
        "job_id": job["id"],
        "heartbeat_at": checked_at,
        "heartbeat_epoch": now_epoch,
        "status": status,
        "lease_owner": job["lease_owner"],
        "attempt": 1,
        "secret_free": True,
    }


def _stale_probe(config: dict[str, Any], checked_at: str, now_epoch: int) -> dict[str, Any] | None:
    probe = config.get("stale_probe", {})
    if not isinstance(probe, dict) or not probe.get("enabled"):
        return None
    age = int(probe.get("last_heartbeat_age_seconds", 0))
    return {
        "job_id": str(probe.get("job_id", "v2c-stale-job-detection-probe")),
        "last_heartbeat_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - age)),
        "last_heartbeat_epoch": now_epoch - age,
        "checked_at": checked_at,
        "age_seconds": age,
        "secret_free": True,
    }


def _detect_stale(records: list[dict[str, Any]], stale_after_seconds: int, now_epoch: int) -> list[dict[str, Any]]:
    stale: list[dict[str, Any]] = []
    for record in records:
        age = now_epoch - int(record.get("last_heartbeat_epoch", record.get("heartbeat_epoch", now_epoch)))
        if age > stale_after_seconds:
            stale.append(
                {
                    "job_id": record.get("job_id"),
                    "age_seconds": age,
                    "stale_after_seconds": stale_after_seconds,
                    "decision": "stale_job_detected",
                }
            )
    return stale


def _memory_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# V2.0C Long-Running Job Heartbeat Proof",
            "",
            f"- Time: {report['checked_at']}",
            f"- Issue: {report['issue_id']}",
            f"- Mode: {report['mode']}",
            f"- Decision: {report['decision']}",
            f"- Job: {report['job_packet']['id']}",
            f"- Heartbeat result: {report['heartbeat_result']['decision']}",
            f"- Stale jobs detected: {len(report['stale_jobs'])}",
            f"- Audit ledger: {report['audit_ledger']}",
            "",
            "## Scope",
            "",
            "One resumable job packet, one heartbeat ledger record, and one stale-job detector pass.",
            "",
            "## Rollback",
            "",
            report["rollback"],
            "",
        ]
    )


def _markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# V2.0C Long-Running Job Heartbeat Proof",
            "",
            f"Checked at: `{report['checked_at']}`",
            f"Status: `{report['status']}`",
            f"Mode: `{report['mode']}`",
            f"Live requested: `{report['live_requested']}`",
            f"Decision: `{report['decision']}`",
            f"Job: `{report['job_packet']['id']}`",
            "",
            "## Results",
            "",
            f"- Job packet: `{report['job_result']['decision']}`",
            f"- Heartbeat: `{report['heartbeat_result']['decision']}`",
            f"- Stale jobs detected: `{len(report['stale_jobs'])}`",
            "",
            "## Audit",
            "",
            f"- `{report['audit_ledger']}`",
            f"- `{report['heartbeat_ledger']}`",
            f"- `{report['memory_markdown']}`",
            "",
        ]
    )


def run(config_path: Path, environ: dict[str, str] | None = None) -> dict[str, Any]:
    config = _load(config_path)
    checked_at = _checked_at()
    now_epoch = _epoch()
    live_requested = _is_live_requested(config, environ)
    live_enabled = bool(config.get("live_enabled"))

    if not live_requested:
        decision = "dry_run_ready"
    elif not live_enabled:
        decision = "blocked_live_not_enabled"
    else:
        decision = "live_ready"

    job = _job_packet(config, checked_at, now_epoch, decision)
    heartbeat = _heartbeat(job, checked_at, now_epoch, decision)
    stale_records = [heartbeat]
    probe = _stale_probe(config, checked_at, now_epoch)
    if probe:
        stale_records.append(probe)
    stale_jobs = _detect_stale(stale_records, int(config.get("stale_after_seconds", 180)), now_epoch)

    write_decision = (
        "written_dry_run"
        if decision == "dry_run_ready"
        else "written_live_ready"
        if decision == "live_ready"
        else "blocked_not_written"
    )
    job_result = {"decision": write_decision, "path": str(Path(config["job_dir"]) / f"{job['id']}.json")}
    heartbeat_result = {"decision": write_decision, "path": str(config["heartbeat_ledger"])}

    ok = decision in {"dry_run_ready", "live_ready"} and bool(job["id"]) and heartbeat["job_id"] == job["id"]
    report = {
        "ok": ok,
        "status": "pass" if ok else "blocked",
        "checked_at": checked_at,
        "config": str(config_path),
        "mode": config.get("mode", "dry_run"),
        "issue_id": str(config.get("issue_id", "")),
        "actor": str(config.get("actor", "")),
        "live_requested": live_requested,
        "live_enabled": live_enabled,
        "decision": decision,
        "job_packet": job,
        "heartbeat": heartbeat,
        "stale_probe": probe,
        "stale_jobs": stale_jobs,
        "job_result": job_result,
        "heartbeat_result": heartbeat_result,
        "rollback": "Cancel the queued job, release the lease, and mark the audit disposition blocked.",
        "audit_ledger": str(config["audit_ledger"]),
        "heartbeat_ledger": str(config["heartbeat_ledger"]),
        "memory_markdown": str(config["memory_markdown"]),
        "secret_free": True,
    }

    ledger = {
        "action_id": "v2.0C-long-running-job-heartbeat",
        "checked_at": checked_at,
        "issue_id": str(config.get("issue_id", "")),
        "actor": str(config.get("actor", "")),
        "capability": "long_running_agent_jobs",
        "decision": decision,
        "job_id": job["id"],
        "heartbeat_seconds": job["heartbeat_seconds"],
        "stale_jobs": len(stale_jobs),
        "input_hash": _digest({"job": job, "heartbeat": heartbeat, "probe": probe}),
        "output_hash": _digest(_redact(report)),
        "rollback": report["rollback"],
        "secret_free": True,
    }

    if ok:
        job_path = Path(job_result["path"])
        job_path.parent.mkdir(parents=True, exist_ok=True)
        job_path.write_text(json.dumps(job, indent=2) + "\n", encoding="utf-8")

        heartbeat_path = Path(config["heartbeat_ledger"])
        heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
        with heartbeat_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(heartbeat, sort_keys=True) + "\n")

    for path_key, content in [
        ("generated_json", json.dumps(report, indent=2) + "\n"),
        ("generated_markdown", _markdown(report)),
        ("memory_markdown", _memory_markdown(report)),
    ]:
        path = Path(config[path_key])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    audit_path = Path(config["audit_ledger"])
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ledger, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V2.0C long-running job heartbeat proof.")
    parser.add_argument("--config", default="configs/long_running_job_v2_0C.json")
    args = parser.parse_args()
    report = run(Path(args.config))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
