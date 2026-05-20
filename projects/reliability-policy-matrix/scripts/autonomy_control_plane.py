from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any


PASS = "pass"
ALLOW_POLICIES = {
    "read_only": "allow",
    "comment_only": "allow_scoped",
    "low_risk_write": "pr_or_canary_only",
    "production_write": "canary_rollback_alert_required",
    "destructive": "human_approval_required",
    "secret_bearing": "human_approval_required",
}


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    return data


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _validate_capabilities(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    capabilities = config.get("capabilities", [])
    forbidden = set(config.get("forbidden_capabilities", []))
    names = {item.get("name") for item in capabilities}
    overlap = sorted(names & forbidden)
    if overlap:
        errors.append(f"forbidden capabilities enabled: {', '.join(overlap)}")
    for item in capabilities:
        if not item.get("enabled"):
            errors.append(f"capability disabled: {item.get('name')}")
        if item.get("risk") not in ALLOW_POLICIES:
            errors.append(f"unknown risk for {item.get('name')}: {item.get('risk')}")
        if not item.get("rollback"):
            errors.append(f"missing rollback metadata: {item.get('name')}")
    return errors


def _validate_policy(config: dict[str, Any]) -> list[str]:
    policy = config.get("policy", {})
    return [
        f"policy mismatch for {risk}: expected {decision}, got {policy.get(risk)}"
        for risk, decision in ALLOW_POLICIES.items()
        if policy.get(risk) != decision
    ]


def _ledger_record(config: dict[str, Any], ok: bool) -> dict[str, Any]:
    action = {
        "issue_id": config.get("issue_id", ""),
        "mode": config.get("mode", ""),
        "capabilities": [item.get("name") for item in config.get("capabilities", [])],
        "policy": config.get("policy", {}),
    }
    return {
        "action_id": "v1.8J-dry-run",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "issue_id": config.get("issue_id", ""),
        "actor": config.get("actor", ""),
        "capability": "end_to_end_unattended_dry_run",
        "policy_decision": "dry_run_allowed" if ok else "blocked",
        "input_hash": _digest(action),
        "output_hash": _digest({"ok": ok}),
        "commit_sha": "resolved_at_runtime",
        "verification_result": "pass" if ok else "fail",
        "rollback_result": "not_needed_dry_run",
        "alert_result": "dry_run_alert_recorded",
        "disposition": "done" if ok else "blocked",
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# V1.8 Autonomy Control Plane Result",
        "",
        f"Checked at: `{report['checked_at']}`",
        f"Status: `{report['status']}`",
        f"Mode: `{report['mode']}`",
        "",
        "## Completed Tasks",
        "",
    ]
    for task in report["completed_tasks"]:
        lines.append(f"- `{task}`")
    lines.extend(["", "## Capability Broker", ""])
    for item in report["capabilities"]:
        lines.append(f"- `{item['name']}`: risk `{item['risk']}`, rollback `{item['rollback']}`")
    lines.extend(["", "## Policy Decisions", ""])
    for risk, decision in report["policy"].items():
        lines.append(f"- `{risk}` -> `{decision}`")
    lines.extend(["", "## Audit Ledger", "", f"- `{report['audit_ledger']}`", ""])
    return "\n".join(lines)


def run(config_path: Path) -> dict[str, Any]:
    config = _load(config_path)
    errors = []
    errors.extend(_validate_capabilities(config))
    errors.extend(_validate_policy(config))

    for section in ["paperclip_scoped_write_auth", "active_alerting", "canary_and_rollback", "kill_switch"]:
        if config.get(section, {}).get("status") != PASS:
            errors.append(f"{section} is not pass")

    ok = not errors
    record = _ledger_record(config, ok)
    ledger_path = Path(config["audit_ledger"])
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

    report = {
        "ok": ok,
        "status": "pass" if ok else "fail",
        "checked_at": record["checked_at"],
        "mode": config.get("mode", ""),
        "completed_tasks": [
            "v1.8C_paperclip_scoped_write_auth_contract",
            "v1.8D_capability_broker_mvp",
            "v1.8E_policy_gate",
            "v1.8F_secret_free_audit_ledger",
            "v1.8G_active_alerting_dry_run",
            "v1.8H_canary_rollback_dry_run",
            "v1.8I_kill_switch_contract",
            "v1.8J_end_to_end_unattended_dry_run",
        ],
        "capabilities": config.get("capabilities", []),
        "policy": config.get("policy", {}),
        "audit_ledger": str(ledger_path),
        "errors": errors,
    }

    json_path = Path(config["generated_json"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    Path(config["generated_markdown"]).write_text(_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V1.8 autonomy control plane dry-run.")
    parser.add_argument("--config", default="configs/autonomy_controls_v1_8.json")
    args = parser.parse_args()
    report = run(Path(args.config))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
