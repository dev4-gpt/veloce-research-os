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
    return env.get(str(config.get("live_enable_env", "VELOCE_CANARY_DEPLOY_LIVE"))) == str(
        config.get("live_enable_value", "1")
    )


def _missing_env(config: dict[str, Any], environ: dict[str, str] | None = None) -> list[str]:
    env = _env(environ)
    return [str(name) for name in config.get("required_live_env", []) if not env.get(str(name))]


def _health_snapshot(names: list[str], checked_at: str, phase: str, decision: str) -> dict[str, Any]:
    return {
        "phase": phase,
        "checked_at": checked_at,
        "decision": "planned_dry_run" if decision == "dry_run_ready" else "planned_live_ready",
        "checks": [
            {
                "name": name,
                "status": "planned",
                "required": True,
                "secret_free": True,
            }
            for name in names
        ],
        "secret_free": True,
    }


def _canary_packet(config: dict[str, Any], checked_at: str, decision: str) -> dict[str, Any]:
    payload = {
        "issue_id": str(config.get("issue_id", "")),
        "candidate_id": str(config.get("candidate_id", "")),
        "candidate_kind": str(config.get("candidate_kind", "")),
        "target_environment": str(config.get("target_environment", "canary")),
        "pre_health_checks": config.get("pre_health_checks", []),
        "post_health_checks": config.get("post_health_checks", []),
    }
    if decision == "dry_run_ready":
        status = "candidate_dry_run_ready"
    elif decision == "live_ready":
        status = "candidate_live_ready"
    else:
        status = "blocked"
    return {
        **payload,
        "status": status,
        "created_at": checked_at,
        "description": str(config.get("candidate_description", "")),
        "input_hash": _digest(payload),
        "production_mutation_performed": False,
        "secret_free": True,
    }


def _rollback_packet(config: dict[str, Any], checked_at: str, canary: dict[str, Any], decision: str) -> dict[str, Any]:
    return {
        "candidate_id": canary["candidate_id"],
        "created_at": checked_at,
        "decision": "rollback_packet_ready" if decision in {"dry_run_ready", "live_ready"} else "blocked",
        "strategy": str(config.get("rollback_strategy", "restore_last_known_good_and_verify_stack_health")),
        "requires_human_confirmation": True,
        "verification": ["stack_health", "knowledge_graph_status"],
        "production_rollback_performed": False,
        "secret_free": True,
    }


def _alert_packet(config: dict[str, Any], checked_at: str, canary: dict[str, Any], stale: bool = False) -> dict[str, Any]:
    return {
        "candidate_id": canary["candidate_id"],
        "created_at": checked_at,
        "event_type": "canary_deploy_proof",
        "severity": "info" if not stale else "warning",
        "channels": config.get("alert_channels", ["audit_ledger"]),
        "message": "V2.0D canary deploy proof prepared rollback and health gates.",
        "sent": False,
        "secret_free": True,
    }


def _memory_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# V2.0D Chat-to-Canary Deploy Proof",
            "",
            f"- Time: {report['checked_at']}",
            f"- Issue: {report['issue_id']}",
            f"- Mode: {report['mode']}",
            f"- Decision: {report['decision']}",
            f"- Candidate: {report['canary_packet']['candidate_id']}",
            f"- Pre-health checks: {len(report['pre_health_snapshot']['checks'])}",
            f"- Post-health checks: {len(report['post_health_snapshot']['checks'])}",
            f"- Rollback decision: {report['rollback_packet']['decision']}",
            f"- Audit ledger: {report['audit_ledger']}",
            "",
            "## Scope",
            "",
            "No-op canary candidate, pre/post health snapshots, rollback packet, and alert packet.",
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
            "# V2.0D Chat-to-Canary Deploy Proof",
            "",
            f"Checked at: `{report['checked_at']}`",
            f"Status: `{report['status']}`",
            f"Mode: `{report['mode']}`",
            f"Live requested: `{report['live_requested']}`",
            f"Decision: `{report['decision']}`",
            f"Candidate: `{report['canary_packet']['candidate_id']}`",
            f"Production mutation performed: `{report['production_mutation_performed']}`",
            "",
            "## Results",
            "",
            f"- Canary packet: `{report['canary_result']['decision']}`",
            f"- Rollback packet: `{report['rollback_result']['decision']}`",
            f"- Alert packet: `{report['alert_result']['decision']}`",
            "",
            "## Audit",
            "",
            f"- `{report['audit_ledger']}`",
            f"- `{report['memory_markdown']}`",
            "",
        ]
    )


def run(config_path: Path, environ: dict[str, str] | None = None) -> dict[str, Any]:
    config = _load(config_path)
    checked_at = _checked_at()
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

    canary = _canary_packet(config, checked_at, decision)
    pre_health = _health_snapshot([str(item) for item in config.get("pre_health_checks", [])], checked_at, "pre", decision)
    post_health = _health_snapshot(
        [str(item) for item in config.get("post_health_checks", [])], checked_at, "post", decision
    )
    rollback_packet = _rollback_packet(config, checked_at, canary, decision)
    alert_packet = _alert_packet(config, checked_at, canary)

    ok = decision in {"dry_run_ready", "live_ready"} and bool(canary["candidate_id"])
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
        "canary_packet": canary,
        "pre_health_snapshot": pre_health,
        "post_health_snapshot": post_health,
        "rollback_packet": rollback_packet,
        "alert_packet": alert_packet,
        "canary_result": {"decision": write_decision, "path": str(config["canary_packet"])},
        "rollback_result": {"decision": write_decision, "path": str(config["rollback_packet"])},
        "alert_result": {"decision": write_decision, "path": str(config["alert_packet"])},
        "rollback": "Do not promote canary; use rollback packet to restore last-known-good and verify stack health.",
        "audit_ledger": str(config["audit_ledger"]),
        "memory_markdown": str(config["memory_markdown"]),
        "production_mutation_performed": False,
        "secret_free": True,
    }

    ledger = {
        "action_id": "v2.0D-chat-to-canary-deploy",
        "checked_at": checked_at,
        "issue_id": str(config.get("issue_id", "")),
        "actor": str(config.get("actor", "")),
        "capability": "chat_to_canary_deploy",
        "decision": decision,
        "candidate_id": canary["candidate_id"],
        "pre_health_checks": len(pre_health["checks"]),
        "post_health_checks": len(post_health["checks"]),
        "production_mutation_performed": False,
        "input_hash": _digest({"canary": canary, "pre": pre_health, "post": post_health}),
        "output_hash": _digest(_redact(report)),
        "rollback": report["rollback"],
        "secret_free": True,
    }

    if ok:
        for path_key, payload in [
            ("canary_packet", canary),
            ("rollback_packet", rollback_packet),
            ("alert_packet", alert_packet),
        ]:
            path = Path(config[path_key])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

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
    parser = argparse.ArgumentParser(description="Run V2.0D chat-to-canary deploy proof.")
    parser.add_argument("--config", default="configs/canary_deploy_v2_0D.json")
    args = parser.parse_args()
    report = run(Path(args.config))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
