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
    return env.get(str(config.get("live_enable_env", "VELOCE_AGENT_RUNNER_LIVE"))) == str(
        config.get("live_enable_value", "1")
    )


def _missing_env(config: dict[str, Any], environ: dict[str, str] | None = None) -> list[str]:
    env = _env(environ)
    return [str(name) for name in config.get("required_live_env", []) if not env.get(str(name))]


def _job(config: dict[str, Any], checked_at: str, now_epoch: int, decision: str) -> dict[str, Any]:
    payload = {
        "job_id": str(config.get("job_id", "")),
        "issue_id": str(config.get("issue_id", "")),
        "capability": str(config.get("capability", "long_running_agent_jobs")),
        "budget_minutes": int(config.get("budget_minutes", 20)),
        "heartbeat_seconds": int(config.get("heartbeat_seconds", 60)),
        "max_steps": int(config.get("max_steps", 5)),
    }
    return {
        "id": payload["job_id"],
        "issue_id": payload["issue_id"],
        "capability": payload["capability"],
        "status": "runner_dry_run_ready" if decision == "dry_run_ready" else "runner_live_ready" if decision == "live_ready" else "blocked",
        "lease_owner": str(config.get("lease_owner", "veloce-agent-runner")),
        "created_at": checked_at,
        "created_epoch": now_epoch,
        "budget_minutes": payload["budget_minutes"],
        "heartbeat_seconds": payload["heartbeat_seconds"],
        "max_steps": payload["max_steps"],
        "input_hash": _digest(payload),
        "secret_free": True,
    }


def _runner_events(config: dict[str, Any], job: dict[str, Any], checked_at: str, now_epoch: int, decision: str) -> list[dict[str, Any]]:
    requested_steps = [str(item) for item in config.get("planned_steps", [])]
    steps = requested_steps[: int(job["max_steps"])]
    events = [
        {
            "event": "lease_acquired",
            "job_id": job["id"],
            "at": checked_at,
            "epoch": now_epoch,
            "lease_owner": job["lease_owner"],
            "decision": decision,
            "secret_free": True,
        }
    ]
    for index, step in enumerate(steps, start=1):
        events.append(
            {
                "event": "step_planned",
                "job_id": job["id"],
                "step": index,
                "description": step,
                "status": "planned_dry_run" if decision == "dry_run_ready" else "planned_live_ready",
                "secret_free": True,
            }
        )
        events.append(
            {
                "event": "heartbeat",
                "job_id": job["id"],
                "step": index,
                "heartbeat_at": checked_at,
                "heartbeat_epoch": now_epoch + index,
                "secret_free": True,
            }
        )
    events.append(
        {
            "event": "lease_released",
            "job_id": job["id"],
            "at": checked_at,
            "epoch": now_epoch + len(steps) + 1,
            "status": "completed_dry_run" if decision == "dry_run_ready" else "completed_live_ready",
            "secret_free": True,
        }
    )
    return events


def _memory_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# V2.0I Long-Running Agent Runner",
            "",
            f"- Time: {report['checked_at']}",
            f"- Issue: {report['issue_id']}",
            f"- Mode: {report['mode']}",
            f"- Decision: {report['decision']}",
            f"- Job: {report['job_packet']['id']}",
            f"- Runner events: {len(report['runner_events'])}",
            f"- Audit ledger: {report['audit_ledger']}",
            "",
            "## Scope",
            "",
            "Lease acquisition, bounded step loop, heartbeat records, cancellation packet, and evidence handoff.",
            "",
            "## Safety Boundary",
            "",
            "The runner records planned work and heartbeats. It does not execute arbitrary shell or production mutations.",
            "",
        ]
    )


def _markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# V2.0I Long-Running Agent Runner",
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
            f"- Runner ledger: `{report['runner_result']['decision']}`",
            f"- Cancellation packet: `{report['cancel_result']['decision']}`",
            "",
            "## Audit",
            "",
            f"- `{report['audit_ledger']}`",
            f"- `{report['runner_ledger']}`",
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
    missing_env = _missing_env(config, environ)

    if not live_requested:
        decision = "dry_run_ready"
    elif not live_enabled:
        decision = "blocked_live_not_enabled"
    elif missing_env:
        decision = "blocked_missing_env"
    else:
        decision = "live_ready"

    job = _job(config, checked_at, now_epoch, decision)
    events = _runner_events(config, job, checked_at, now_epoch, decision) if decision in {"dry_run_ready", "live_ready"} else []
    cancel_packet = {
        "job_id": job["id"],
        "created_at": checked_at,
        "decision": "cancel_packet_ready" if decision in {"dry_run_ready", "live_ready"} else "blocked",
        "release_lease": True,
        "mark_disposition": "blocked",
        "secret_free": True,
    }
    ok = decision in {"dry_run_ready", "live_ready"} and bool(job["id"]) and bool(events)
    write_decision = (
        "written_dry_run"
        if decision == "dry_run_ready"
        else "written_live_ready"
        if decision == "live_ready"
        else "blocked_not_written"
    )
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
        "missing_env": missing_env if live_requested else [],
        "decision": decision,
        "job_packet": job,
        "runner_events": events,
        "cancel_packet": cancel_packet,
        "job_result": {"decision": write_decision, "path": str(Path(config["job_dir"]) / f"{job['id']}.json")},
        "runner_result": {"decision": write_decision, "path": str(config["runner_ledger"])},
        "cancel_result": {"decision": write_decision, "path": str(config["cancel_packet"])},
        "audit_ledger": str(config["audit_ledger"]),
        "runner_ledger": str(config["runner_ledger"]),
        "memory_markdown": str(config["memory_markdown"]),
        "production_mutation_performed": False,
        "secret_free": True,
    }

    ledger = {
        "action_id": "v2.0I-long-running-agent-runner",
        "checked_at": checked_at,
        "issue_id": str(config.get("issue_id", "")),
        "actor": str(config.get("actor", "")),
        "capability": "long_running_agent_jobs",
        "decision": decision,
        "job_id": job["id"],
        "events": len(events),
        "input_hash": _digest(job),
        "output_hash": _digest(_redact(report)),
        "production_mutation_performed": False,
        "secret_free": True,
    }

    if ok:
        job_dir = Path(config["job_dir"])
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / f"{job['id']}.json").write_text(json.dumps(job, indent=2) + "\n", encoding="utf-8")
        Path(config["cancel_packet"]).parent.mkdir(parents=True, exist_ok=True)
        Path(config["cancel_packet"]).write_text(json.dumps(cancel_packet, indent=2) + "\n", encoding="utf-8")
        runner_path = Path(config["runner_ledger"])
        runner_path.parent.mkdir(parents=True, exist_ok=True)
        runner_path.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")

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
    parser = argparse.ArgumentParser(description="Run V2.0I long-running agent runner proof.")
    parser.add_argument("--config", default="configs/agent_runner_v2_0I.json")
    args = parser.parse_args()
    report = run(Path(args.config))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
