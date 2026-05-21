from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any


ALLOW_POLICIES = {
    "read_only": "allow",
    "comment_only": "allow_scoped",
    "low_risk_write": "pr_or_canary_only",
    "production_write": "canary_rollback_alert_required",
    "destructive": "human_approval_required",
    "secret_bearing": "human_approval_required",
}

LIVE_BLOCKED_RISKS = {"destructive", "secret_bearing"}


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    return data


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _checked_at() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _is_live_enabled(config: dict[str, Any], environ: dict[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return env.get(str(config.get("live_enable_env", "VELOCE_V2_LIVE"))) == str(
        config.get("live_enable_value", "1")
    )


def _kill_switch_active(config: dict[str, Any]) -> bool:
    kill_switch = str(config.get("kill_switch_path", ""))
    return bool(kill_switch and Path(kill_switch).exists())


def _missing_env(capability: str, config: dict[str, Any], environ: dict[str, str] | None = None) -> list[str]:
    env = environ if environ is not None else os.environ
    required = config.get("required_live_env", {}).get(capability, [])
    return [name for name in required if not env.get(name)]


def _validate_policy(config: dict[str, Any]) -> list[str]:
    policy = config.get("policy", {})
    return [
        f"policy mismatch for {risk}: expected {decision}, got {policy.get(risk)}"
        for risk, decision in ALLOW_POLICIES.items()
        if policy.get(risk) != decision
    ]


def _validate_capabilities(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    capabilities = config.get("capabilities", [])
    forbidden = set(config.get("forbidden_capabilities", []))
    names = {item.get("name") for item in capabilities}
    overlap = sorted(names & forbidden)
    if overlap:
        errors.append(f"forbidden capabilities enabled: {', '.join(overlap)}")
    for item in capabilities:
        name = item.get("name")
        if not item.get("enabled"):
            errors.append(f"capability disabled: {name}")
        risk = item.get("risk")
        if risk not in ALLOW_POLICIES:
            errors.append(f"unknown risk for {name}: {risk}")
        if not item.get("rollback"):
            errors.append(f"missing rollback metadata: {name}")
        if item.get("live_enabled") and risk in LIVE_BLOCKED_RISKS:
            errors.append(f"{name} cannot be live_enabled with risk {risk}")
    return errors


def _capability_decision(
    capability: dict[str, Any],
    config: dict[str, Any],
    live_requested: bool,
    kill_switch_active: bool,
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    name = str(capability.get("name", ""))
    risk = str(capability.get("risk", ""))
    env = environ if environ is not None else os.environ
    missing = _missing_env(name, config, environ)
    live_enabled = bool(capability.get("live_enabled"))

    if kill_switch_active:
        decision = "blocked_kill_switch"
    elif not capability.get("enabled"):
        decision = "blocked_disabled"
    elif not live_requested:
        decision = "dry_run_ready"
    elif not live_enabled:
        decision = "blocked_live_not_enabled"
    elif missing:
        decision = "blocked_missing_live_env"
    elif risk in LIVE_BLOCKED_RISKS:
        decision = "blocked_human_approval_required"
    elif risk == "production_write" and env.get("VELOCE_CANARY_APPROVED") != "1":
        decision = "blocked_canary_approval_required"
    else:
        decision = "live_ready"

    return {
        "name": name,
        "risk": risk,
        "policy": config.get("policy", {}).get(risk, "unknown"),
        "decision": decision,
        "live_requested": live_requested,
        "live_enabled": live_enabled,
        "missing_env": missing,
        "rollback": capability.get("rollback", ""),
        "description": capability.get("description", ""),
    }


def _job_packets(config: dict[str, Any], decisions: list[dict[str, Any]], checked_at: str) -> list[dict[str, Any]]:
    decision_by_name = {item["name"]: item for item in decisions}
    packets = []
    for template in config.get("job_templates", []):
        capability = template.get("capability", "")
        decision = decision_by_name.get(capability, {})
        packets.append(
            {
                "id": template.get("id", ""),
                "issue_id": config.get("issue_id", ""),
                "capability": capability,
                "status": "queued_dry_run" if decision.get("decision") == "dry_run_ready" else "blocked",
                "policy_decision": decision.get("decision", "unknown"),
                "budget_minutes": template.get("budget_minutes", 0),
                "max_attempts": template.get("max_attempts", 1),
                "heartbeat_seconds": template.get("heartbeat_seconds", 60),
                "lease_owner": config.get("actor", ""),
                "created_at": checked_at,
                "input_hash": _digest(template),
                "secret_free": True,
            }
        )
    return packets


def _write_job_packets(job_dir: Path, packets: list[dict[str, Any]]) -> None:
    job_dir.mkdir(parents=True, exist_ok=True)
    for packet in packets:
        path = job_dir / f"{packet['id']}.json"
        path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ledger_records(config: dict[str, Any], decisions: list[dict[str, Any]], checked_at: str) -> list[dict[str, Any]]:
    records = []
    for decision in decisions:
        records.append(
            {
                "action_id": f"v2.0-{decision['name']}",
                "checked_at": checked_at,
                "issue_id": config.get("issue_id", ""),
                "actor": config.get("actor", ""),
                "capability": decision["name"],
                "risk": decision["risk"],
                "policy_decision": decision["decision"],
                "input_hash": _digest({"capability": decision["name"], "issue_id": config.get("issue_id", "")}),
                "output_hash": _digest(decision),
                "commit_sha": "resolved_at_runtime",
                "verification_result": "pending_live" if decision["decision"] == "live_ready" else "dry_run_recorded",
                "rollback_result": "prepared",
                "alert_result": "prepared",
                "disposition": "ready" if decision["decision"] in {"dry_run_ready", "live_ready"} else "blocked",
                "secret_free": True,
            }
        )
    return records


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# V2.0 Production Execution Control Plane",
        "",
        f"Checked at: `{report['checked_at']}`",
        f"Status: `{report['status']}`",
        f"Mode: `{report['mode']}`",
        f"Live requested: `{report['live_requested']}`",
        f"Kill switch active: `{report['kill_switch_active']}`",
        "",
        "## Capability Decisions",
        "",
        "| Capability | Risk | Decision | Rollback |",
        "|---|---|---|---|",
    ]
    for item in report["decisions"]:
        lines.append(
            f"| `{item['name']}` | `{item['risk']}` | `{item['decision']}` | {item['rollback']} |"
        )
    lines.extend(["", "## Long-Running Job Packets", ""])
    for packet in report["job_packets"]:
        lines.append(
            f"- `{packet['id']}`: capability `{packet['capability']}`, status `{packet['status']}`, heartbeat `{packet['heartbeat_seconds']}s`"
        )
    lines.extend(["", "## Audit Ledger", "", f"- `{report['audit_ledger']}`", ""])
    return "\n".join(lines)


def run(config_path: Path, environ: dict[str, str] | None = None) -> dict[str, Any]:
    config = _load(config_path)
    checked_at = _checked_at()
    live_requested = _is_live_enabled(config, environ)
    kill_switch_active = _kill_switch_active(config)
    errors = []
    errors.extend(_validate_policy(config))
    errors.extend(_validate_capabilities(config))

    decisions = [
        _capability_decision(item, config, live_requested, kill_switch_active, environ)
        for item in config.get("capabilities", [])
    ]
    blocked = [item for item in decisions if item["decision"].startswith("blocked")]
    if live_requested and blocked:
        errors.append("live execution requested but one or more capabilities are blocked")

    job_packets = _job_packets(config, decisions, checked_at)
    job_dir = Path(config["job_dir"])
    _write_job_packets(job_dir, job_packets)

    ledger_records = _ledger_records(config, decisions, checked_at)
    ledger_path = Path(config["audit_ledger"])
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in ledger_records),
        encoding="utf-8",
    )

    ok = not errors and not (live_requested and blocked)
    report = {
        "ok": ok,
        "status": "pass" if ok else "blocked",
        "checked_at": checked_at,
        "config": str(config_path),
        "target_state": config.get("target_state", ""),
        "mode": config.get("mode", ""),
        "live_requested": live_requested,
        "kill_switch_active": kill_switch_active,
        "decisions": decisions,
        "job_packets": job_packets,
        "audit_ledger": str(ledger_path),
        "job_dir": str(job_dir),
        "errors": errors,
        "next_action": (
            "Enable live capability flags and scoped env tokens one capability at a time."
            if not live_requested
            else "Resolve blocked live capability gates before unattended production execution."
        ),
    }

    json_path = Path(config["generated_json"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    Path(config["generated_markdown"]).write_text(_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V2.0 production execution control plane.")
    parser.add_argument("--config", default="configs/production_execution_v2_0.json")
    args = parser.parse_args()
    report = run(Path(args.config))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
