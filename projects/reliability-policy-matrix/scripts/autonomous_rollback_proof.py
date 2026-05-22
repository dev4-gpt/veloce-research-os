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
    return env.get(str(config.get("live_enable_env", "VELOCE_ROLLBACK_LIVE"))) == str(
        config.get("live_enable_value", "1")
    )


def _missing_env(config: dict[str, Any], environ: dict[str, str] | None = None) -> list[str]:
    env = _env(environ)
    return [str(name) for name in config.get("required_live_env", []) if not env.get(str(name))]


def _rollback_packet(config: dict[str, Any], checked_at: str, decision: str) -> dict[str, Any]:
    payload = {
        "issue_id": str(config.get("issue_id", "")),
        "rollback_id": str(config.get("rollback_id", "")),
        "target_environment": str(config.get("target_environment", "production")),
        "last_known_good_ref": str(config.get("last_known_good_ref", "")),
        "rollback_strategy": str(config.get("rollback_strategy", "")),
        "pre_checks": [str(item) for item in config.get("pre_checks", [])],
        "post_checks": [str(item) for item in config.get("post_checks", [])],
    }
    return {
        **payload,
        "created_at": checked_at,
        "status": "rollback_dry_run_ready" if decision == "dry_run_ready" else "rollback_live_ready" if decision == "live_ready" else "blocked",
        "requires_human_confirmation": True,
        "input_hash": _digest(payload),
        "production_rollback_performed": False,
        "secret_free": True,
    }


def _verification_packet(config: dict[str, Any], checked_at: str, phase: str, decision: str) -> dict[str, Any]:
    checks = config.get(f"{phase}_checks", [])
    return {
        "phase": phase,
        "checked_at": checked_at,
        "decision": "planned_dry_run" if decision == "dry_run_ready" else "planned_live_ready" if decision == "live_ready" else "blocked",
        "checks": [
            {
                "name": str(name),
                "status": "planned",
                "required": True,
                "secret_free": True,
            }
            for name in checks
        ],
        "secret_free": True,
    }


def _alert_packet(config: dict[str, Any], checked_at: str, rollback: dict[str, Any], decision: str) -> dict[str, Any]:
    return {
        "rollback_id": rollback["rollback_id"],
        "created_at": checked_at,
        "event_type": "autonomous_rollback_proof",
        "severity": "warning",
        "channels": config.get("alert_channels", ["audit_ledger"]),
        "message": "V2.0E rollback proof prepared restore, verification, and escalation packets.",
        "sent": False,
        "decision": "alert_dry_run_ready" if decision == "dry_run_ready" else "alert_live_ready" if decision == "live_ready" else "blocked",
        "secret_free": True,
    }


def _memory_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# V2.0E Autonomous Rollback Proof",
            "",
            f"- Time: {report['checked_at']}",
            f"- Issue: {report['issue_id']}",
            f"- Mode: {report['mode']}",
            f"- Decision: {report['decision']}",
            f"- Rollback: {report['rollback_packet']['rollback_id']}",
            f"- Production rollback performed: {report['production_rollback_performed']}",
            f"- Audit ledger: {report['audit_ledger']}",
            "",
            "## Scope",
            "",
            "Rollback packet, pre/post verification packets, alert packet, and escalation notes.",
            "",
            "## Safety Boundary",
            "",
            "The proof prepares rollback evidence but does not run destructive production commands.",
            "",
        ]
    )


def _markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# V2.0E Autonomous Rollback Proof",
            "",
            f"Checked at: `{report['checked_at']}`",
            f"Status: `{report['status']}`",
            f"Mode: `{report['mode']}`",
            f"Live requested: `{report['live_requested']}`",
            f"Decision: `{report['decision']}`",
            f"Rollback: `{report['rollback_packet']['rollback_id']}`",
            f"Production rollback performed: `{report['production_rollback_performed']}`",
            "",
            "## Results",
            "",
            f"- Rollback packet: `{report['rollback_result']['decision']}`",
            f"- Verification packet: `{report['verification_result']['decision']}`",
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

    rollback = _rollback_packet(config, checked_at, decision)
    pre_verification = _verification_packet(config, checked_at, "pre", decision)
    post_verification = _verification_packet(config, checked_at, "post", decision)
    alert = _alert_packet(config, checked_at, rollback, decision)
    ok = decision in {"dry_run_ready", "live_ready"} and bool(rollback["rollback_id"])
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
        "rollback_packet": rollback,
        "pre_verification_packet": pre_verification,
        "post_verification_packet": post_verification,
        "alert_packet": alert,
        "rollback_result": {"decision": write_decision, "path": str(config["rollback_packet"])},
        "verification_result": {"decision": write_decision, "path": str(config["verification_packet"])},
        "alert_result": {"decision": write_decision, "path": str(config["alert_packet"])},
        "production_rollback_performed": False,
        "audit_ledger": str(config["audit_ledger"]),
        "memory_markdown": str(config["memory_markdown"]),
        "secret_free": True,
    }

    ledger = {
        "action_id": "v2.0E-autonomous-rollback",
        "checked_at": checked_at,
        "issue_id": str(config.get("issue_id", "")),
        "actor": str(config.get("actor", "")),
        "capability": "autonomous_rollback",
        "decision": decision,
        "rollback_id": rollback["rollback_id"],
        "production_rollback_performed": False,
        "input_hash": _digest(rollback),
        "output_hash": _digest(_redact(report)),
        "verification_result": "prepared",
        "alert_result": "prepared",
        "secret_free": True,
    }

    if ok:
        for path_key, payload in [
            ("rollback_packet", rollback),
            ("verification_packet", {"pre": pre_verification, "post": post_verification, "secret_free": True}),
            ("alert_packet", alert),
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
    parser = argparse.ArgumentParser(description="Run V2.0E autonomous rollback proof.")
    parser.add_argument("--config", default="configs/autonomous_rollback_v2_0E.json")
    args = parser.parse_args()
    report = run(Path(args.config))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
