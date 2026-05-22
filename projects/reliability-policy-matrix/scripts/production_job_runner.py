#!/usr/bin/env python3
"""Durable V2.1 production job runner for typed Veloce execution packets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import uuid
from typing import Any


RUNNER_STATES = {
    "queued_dry_run",
    "approved_for_live_candidate",
    "lease_acquired",
    "running",
    "heartbeat",
    "completed",
    "blocked",
    "cancelled",
    "rollback_required",
    "rollback_prepared",
}

ALLOWED_CAPABILITIES = {
    "paperclip_writeback",
    "chat_to_pr",
    "chat_to_canary_deploy",
    "autonomous_rollback",
    "long_running_agent_jobs",
    "active_alerting",
    "graph_memory_ingestion",
}

FORBIDDEN_KEYS = {
    "command",
    "shell",
    "docker",
    "token",
    "api_key",
    "secret",
    "password",
    "path",
    "filesystem",
    "raw",
}

SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|bearer\s+[a-z0-9._~+/=-]{16,}|sk-[a-z0-9]{12,}|nvapi-[a-z0-9_-]{12,})"
)


def _load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _checked_at() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _epoch() -> int:
    return int(time.time())


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "").strip()).strip("-")
    return safe[:96]


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    text = str(value)
    return SECRET_PATTERN.sub("[redacted]", text)


def _payload_has_forbidden_keys(payload: Any) -> list[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key).lower()
            if key_text in FORBIDDEN_KEYS or key_text.endswith(("_token", "_secret", "_password", "_api_key")):
                found.add(str(key))
            found.update(_payload_has_forbidden_keys(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_payload_has_forbidden_keys(item))
    return sorted(found)


def _payload_has_secret(payload: Any) -> bool:
    if isinstance(payload, dict):
        return any(_payload_has_secret(value) for value in payload.values())
    if isinstance(payload, list):
        return any(_payload_has_secret(value) for value in payload)
    if isinstance(payload, (bool, int, float)) or payload is None:
        return False
    return bool(SECRET_PATTERN.search(str(payload)))


def _load_config(config_path: Path) -> dict[str, Any]:
    config = _load_json(config_path)
    if not isinstance(config, dict):
        raise ValueError("runner config must be a JSON object")
    return config


def _job_dir(config: dict[str, Any]) -> Path:
    return Path(config["job_dir"])


def _state_dir(config: dict[str, Any]) -> Path:
    return Path(config["state_dir"])


def _audit_ledger(config: dict[str, Any]) -> Path:
    return Path(config["audit_ledger"])


def _runner_ledger(config: dict[str, Any]) -> Path:
    return Path(config["runner_ledger"])


def _memory_dir(config: dict[str, Any]) -> Path:
    return Path(config["memory_dir"])


def _job_path(config: dict[str, Any], job_id: str) -> Path:
    return _job_dir(config) / f"{_safe_id(job_id)}.json"


def _state_path(config: dict[str, Any], job_id: str) -> Path:
    return _state_dir(config) / f"{_safe_id(job_id)}.json"


def _load_job(config: dict[str, Any], job_id: str) -> dict[str, Any] | None:
    job = _load_json(_job_path(config, job_id), None)
    return job if isinstance(job, dict) else None


def _load_state(config: dict[str, Any], job_id: str) -> dict[str, Any]:
    state = _load_json(_state_path(config, job_id), {})
    if not isinstance(state, dict):
        state = {}
    return state


def _write_state(config: dict[str, Any], job_id: str, state: dict[str, Any]) -> None:
    _write_json(_state_path(config, job_id), state)


def _base_state(job: dict[str, Any]) -> dict[str, Any]:
    now = _checked_at()
    return {
        "job_id": job["id"],
        "capability": job["capability"],
        "state": job.get("status", "queued_dry_run"),
        "attempts": 0,
        "lease_owner": "",
        "lease_expires_at": 0,
        "last_heartbeat_at": "",
        "last_transition_at": now,
        "trace_id": str(uuid.uuid4()),
        "idempotency_key": _digest({"job_id": job["id"], "capability": job["capability"]}),
        "job_input_hash": job.get("input_hash", ""),
        "secret_free": True,
    }


def _event(
    config: dict[str, Any],
    state: dict[str, Any],
    transition: str,
    decision: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "checked_at": _checked_at(),
        "trace_id": state.get("trace_id") or str(uuid.uuid4()),
        "job_id": state.get("job_id", ""),
        "capability": state.get("capability", ""),
        "transition": transition,
        "state": state.get("state", ""),
        "decision": decision,
        "attempts": state.get("attempts", 0),
        "idempotency_key": state.get("idempotency_key", ""),
        "details": _redact(details or {}),
        "secret_free": True,
    }
    _append_jsonl(_runner_ledger(config), event)
    _append_jsonl(_audit_ledger(config), event)
    _write_memory_markdown(config, event)
    return event


def _write_memory_markdown(config: dict[str, Any], event: dict[str, Any]) -> None:
    memory_dir = _memory_dir(config)
    memory_dir.mkdir(parents=True, exist_ok=True)
    name = f"{event['checked_at'].replace(':', '').replace('-', '')}-{_safe_id(event['job_id'])}-{event['transition']}.md"
    lines = [
        f"# Production Job Event {event['job_id']}",
        "",
        f"- Time: {event['checked_at']}",
        f"- Trace ID: {event['trace_id']}",
        f"- Capability: {event['capability']}",
        f"- Transition: {event['transition']}",
        f"- State: {event['state']}",
        f"- Decision: {event['decision']}",
        "",
        "## Graph Sink",
        "",
        "OpenWebUI -> MCPO production execution API -> V2.1 durable runner -> audit ledger -> Obsidian/Graphify memory.",
        "",
    ]
    (memory_dir / name).write_text("\n".join(lines), encoding="utf-8")


def validate_packet(packet: dict[str, Any]) -> list[str]:
    errors = []
    job_id = _safe_id(str(packet.get("id", "")))
    capability = str(packet.get("capability", ""))
    state = str(packet.get("status", "queued_dry_run"))
    if not job_id:
        errors.append("job id is required")
    if capability not in ALLOWED_CAPABILITIES:
        errors.append(f"capability is not allowlisted: {capability}")
    if state not in RUNNER_STATES:
        errors.append(f"unknown state: {state}")
    forbidden = _payload_has_forbidden_keys(packet)
    if forbidden:
        errors.append(f"forbidden packet keys: {', '.join(forbidden)}")
    if _payload_has_secret(packet):
        errors.append("secret-like content is not allowed in job packets")
    return errors


def enqueue_job(config: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    job_id = _safe_id(str(packet.get("id", "")))
    capability = str(packet.get("capability", ""))
    if job_id:
        packet["id"] = job_id
    packet.setdefault("issue_id", config.get("issue_id", "VEL-v2.1"))
    packet.setdefault("status", "queued_dry_run")
    packet.setdefault("policy_decision", "dry_run_ready")
    packet.setdefault("budget_minutes", 5)
    packet.setdefault("max_attempts", 1)
    packet.setdefault("heartbeat_seconds", 60)
    packet.setdefault("lease_owner", "")
    packet.setdefault("created_at", _checked_at())
    packet.setdefault("input_hash", _digest(packet))
    packet.setdefault("secret_free", True)
    errors = validate_packet(packet)
    if errors:
        return _api_response("production_job_enqueue", trace_id, job_id, capability, "blocked_invalid_packet", False, errors)
    _write_json(_job_path(config, job_id), packet)
    state = _base_state(packet)
    _write_state(config, job_id, state)
    event = _event(config, state, "enqueue", "queued_dry_run", {"source": "api"})
    return _api_response(
        "production_job_enqueue",
        trace_id,
        job_id,
        capability,
        "queued_dry_run",
        True,
        audit_refs=[str(_runner_ledger(config)), str(_audit_ledger(config))],
        extra={"job": packet, "state": state, "event": event},
    )


def approve_job(config: dict[str, Any], job_id: str, approved_by: str, approval: str = "human_approved") -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    job_id = _safe_id(job_id)
    job = _load_job(config, job_id)
    if not job:
        return _api_response("production_job_approve", trace_id, job_id, "", "not_found", False, ["job not found"])
    if SECRET_PATTERN.search(approved_by):
        return _api_response("production_job_approve", trace_id, job_id, job.get("capability", ""), "blocked_secret_like_content", False, ["approved_by contains secret-like content"])
    if approval != "human_approved" or not approved_by:
        return _api_response("production_job_approve", trace_id, job_id, job.get("capability", ""), "blocked_missing_human_approval", False, ["human approval is required"])
    state = _load_state(config, job_id) or _base_state(job)
    if state.get("state") in {"completed", "cancelled"}:
        return _api_response("production_job_approve", trace_id, job_id, job.get("capability", ""), "blocked_terminal_state", False, [f"job is already {state.get('state')}"])
    state.update(
        {
            "state": "approved_for_live_candidate",
            "approved_by": approved_by,
            "approved_at": _checked_at(),
            "last_transition_at": _checked_at(),
        }
    )
    job["status"] = "approved_for_live_candidate"
    _write_json(_job_path(config, job_id), job)
    _write_state(config, job_id, state)
    event = _event(config, state, "approve", "approved_for_live_candidate", {"approved_by": approved_by})
    return _api_response("production_job_approve", trace_id, job_id, job.get("capability", ""), "approved_for_live_candidate", True, audit_refs=[str(_runner_ledger(config)), str(_audit_ledger(config))], extra={"state": state, "event": event})


def cancel_job(config: dict[str, Any], job_id: str, reason: str = "operator_cancelled") -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    job_id = _safe_id(job_id)
    job = _load_job(config, job_id)
    if not job:
        return _api_response("production_job_cancel", trace_id, job_id, "", "not_found", False, ["job not found"])
    if SECRET_PATTERN.search(reason):
        return _api_response("production_job_cancel", trace_id, job_id, job.get("capability", ""), "blocked_secret_like_content", False, ["reason contains secret-like content"])
    state = _load_state(config, job_id) or _base_state(job)
    state.update(
        {
            "state": "cancelled",
            "cancel_reason": reason[:240],
            "last_transition_at": _checked_at(),
            "lease_owner": "",
            "lease_expires_at": 0,
        }
    )
    job["status"] = "cancelled"
    _write_json(_job_path(config, job_id), job)
    _write_state(config, job_id, state)
    event = _event(config, state, "cancel", "cancelled", {"reason": reason[:240]})
    return _api_response("production_job_cancel", trace_id, job_id, job.get("capability", ""), "cancelled", True, audit_refs=[str(_runner_ledger(config)), str(_audit_ledger(config))], extra={"state": state, "event": event})


def status(config: dict[str, Any], job_id: str | None = None) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    if job_id:
        safe = _safe_id(job_id)
        job = _load_job(config, safe)
        state = _load_state(config, safe)
        ok = bool(job)
        return _api_response(
            "production_job_status",
            trace_id,
            safe,
            (job or {}).get("capability", ""),
            "status_ready" if ok else "not_found",
            ok,
            [] if ok else ["job not found"],
            audit_refs=[str(_runner_ledger(config)), str(_audit_ledger(config))],
            extra={"job": job, "state": state},
        )
    jobs = []
    for path in sorted(_job_dir(config).glob("*.json")):
        job = _load_json(path, {})
        if not isinstance(job, dict):
            continue
        state = _load_state(config, str(job.get("id", path.stem)))
        jobs.append(
            {
                "job_id": job.get("id", path.stem),
                "capability": job.get("capability", ""),
                "job_status": job.get("status", ""),
                "runner_state": state.get("state", job.get("status", "")),
                "last_transition_at": state.get("last_transition_at", ""),
            }
        )
    return _api_response(
        "production_execution_status",
        trace_id,
        "",
        "",
        "status_ready",
        True,
        audit_refs=[str(_runner_ledger(config)), str(_audit_ledger(config))],
        extra={
            "jobs": jobs,
            "job_count": len(jobs),
            "runner_states": sorted(RUNNER_STATES),
            "mode": config.get("mode", "dry_run"),
        },
    )


def audit_tail(config: dict[str, Any], limit: int = 20) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    limit = max(1, min(int(limit or 20), 100))
    records = []
    for path in (_audit_ledger(config), _runner_ledger(config)):
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
        for line in lines:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    records = records[-limit:]
    return _api_response(
        "production_audit_tail",
        trace_id,
        "",
        "",
        "audit_tail_ready",
        True,
        audit_refs=[str(_runner_ledger(config)), str(_audit_ledger(config))],
        extra={"records": _redact(records), "limit": limit},
    )


def _api_response(
    service: str,
    trace_id: str,
    job_id: str,
    capability: str,
    decision: str,
    ok: bool,
    errors: list[str] | None = None,
    audit_refs: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "ok": ok,
        "service": service,
        "checked_at": _checked_at(),
        "trace_id": trace_id,
        "decision": decision,
        "job_id": job_id,
        "capability": capability,
        "audit_refs": audit_refs or [],
        "errors": errors or [],
        "next_action": "Inspect production_job_status, approve a queued candidate, or run the durable runner once.",
    }
    if extra:
        payload.update(extra)
    return payload


def _acquire_lease(config: dict[str, Any], job: dict[str, Any], state: dict[str, Any], now: int) -> tuple[bool, dict[str, Any]]:
    owner = config.get("lease_owner", "veloce-production-runner")
    stale_after = int(config.get("stale_after_seconds", 300))
    lease_seconds = int(config.get("lease_seconds", 120))
    if state.get("lease_owner") and int(state.get("lease_expires_at", 0)) > now:
        return False, state
    if state.get("lease_owner") and int(state.get("lease_expires_at", 0)) <= now:
        _event(config, state, "stale_lease_recovered", "lease_recovered", {"previous_owner": state.get("lease_owner"), "stale_after_seconds": stale_after})
    state.update(
        {
            "state": "lease_acquired",
            "lease_owner": owner,
            "lease_expires_at": now + lease_seconds,
            "attempts": int(state.get("attempts", 0)) + 1,
            "last_transition_at": _checked_at(),
        }
    )
    _write_state(config, str(job["id"]), state)
    _event(config, state, "lease_acquired", "lease_acquired", {"lease_seconds": lease_seconds})
    return True, state


def _run_job(config: dict[str, Any], job: dict[str, Any]) -> dict[str, Any]:
    job_id = str(job["id"])
    errors = validate_packet(job)
    state = _load_state(config, job_id) or _base_state(job)
    if state.get("job_input_hash") != job.get("input_hash", ""):
        state = _base_state(job)
    if errors:
        state.update({"state": "blocked", "last_transition_at": _checked_at()})
        _write_state(config, job_id, state)
        _event(config, state, "blocked", "blocked_invalid_packet", {"errors": errors})
        return state
    if state.get("state") in {"completed", "cancelled", "blocked"}:
        return state
    max_attempts = int(job.get("max_attempts", 1) or 1)
    if int(state.get("attempts", 0)) >= max_attempts and state.get("state") != "approved_for_live_candidate":
        state.update({"state": "blocked", "last_transition_at": _checked_at()})
        _write_state(config, job_id, state)
        _event(config, state, "blocked", "blocked_max_attempts", {"max_attempts": max_attempts})
        return state
    acquired, state = _acquire_lease(config, job, state, _epoch())
    if not acquired:
        return state
    state.update({"state": "running", "last_transition_at": _checked_at()})
    _write_state(config, job_id, state)
    _event(config, state, "running", "runner_started", {"mode": config.get("mode", "dry_run")})
    state.update({"state": "heartbeat", "last_heartbeat_at": _checked_at(), "last_transition_at": _checked_at()})
    _write_state(config, job_id, state)
    _event(config, state, "heartbeat", "heartbeat_recorded", {"heartbeat_seconds": job.get("heartbeat_seconds", 60)})
    terminal_state = "completed"
    if job.get("capability") == "chat_to_canary_deploy" and config.get("simulate_canary_failure"):
        terminal_state = "rollback_required"
    state.update(
        {
            "state": terminal_state,
            "completed_at": _checked_at() if terminal_state == "completed" else "",
            "last_transition_at": _checked_at(),
            "lease_owner": "",
            "lease_expires_at": 0,
            "production_mutation_performed": False,
        }
    )
    job["status"] = terminal_state
    _write_json(_job_path(config, job_id), job)
    _write_state(config, job_id, state)
    _event(config, state, terminal_state, terminal_state, {"production_mutation_performed": False})
    return state


def run_once(config_path: Path, job_id: str | None = None) -> dict[str, Any]:
    config = _load_config(config_path)
    _job_dir(config).mkdir(parents=True, exist_ok=True)
    _state_dir(config).mkdir(parents=True, exist_ok=True)
    jobs: list[dict[str, Any]] = []
    if job_id:
        job = _load_job(config, job_id)
        if job:
            jobs.append(job)
    else:
        for path in sorted(_job_dir(config).glob("*.json")):
            job = _load_json(path, {})
            if isinstance(job, dict):
                jobs.append(job)
    states = [_run_job(config, job) for job in jobs]
    report = {
        "ok": True,
        "service": "production_job_runner",
        "checked_at": _checked_at(),
        "trace_id": str(uuid.uuid4()),
        "decision": "runner_once_complete",
        "jobs_seen": len(jobs),
        "states": states,
        "audit_refs": [str(_runner_ledger(config)), str(_audit_ledger(config))],
        "next_action": "Inspect generated runner events and graph-memory markdown before enabling any live adapter.",
    }
    output_path = Path(config["generated_json"])
    _write_json(output_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the V2.1 durable production job runner.")
    parser.add_argument("--config", default="configs/production_job_runner_v2_1.json")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--action", choices=["run-once", "status", "audit-tail"], default="run-once")
    args = parser.parse_args()
    config_path = Path(args.config)
    if args.action == "run-once":
        result = run_once(config_path, args.job_id or None)
    else:
        config = _load_config(config_path)
        result = status(config, args.job_id or None) if args.action == "status" else audit_tail(config)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
