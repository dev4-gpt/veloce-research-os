#!/usr/bin/env python3
"""Run the V2.6-V3.1 Veloce production AI OS pilot pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
SECRET_KEY_PARTS = ("authorization", "api_key", "apikey", "password", "webhook")
SECRET_KEY_SUFFIXES = ("_token", "-token", " token", "_secret", "-secret", " secret")


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    return data


def _checked_at() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[redacted]" if _is_secret_key(key) else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _is_secret_key(key: str) -> bool:
    normalized = key.lower()
    if normalized in {"token", "secret", "authorization"}:
        return True
    return any(part in normalized for part in SECRET_KEY_PARTS) or normalized.endswith(SECRET_KEY_SUFFIXES)


def _env(environ: dict[str, str] | None = None) -> dict[str, str]:
    return environ if environ is not None else os.environ


def _live_requested(stage: dict[str, Any], config: dict[str, Any], environ: dict[str, str] | None = None) -> bool:
    env = _env(environ)
    global_enabled = env.get(str(config.get("global_live_enable_env", "VELOCE_PRODUCTION_AI_OS_LIVE"))) == str(
        config.get("global_live_enable_value", "1")
    )
    stage_enabled = env.get(str(stage.get("live_enable_env", ""))) == str(stage.get("live_enable_value", "1"))
    return global_enabled and stage_enabled


def _missing_env(stage: dict[str, Any], environ: dict[str, str] | None = None) -> list[str]:
    env = _env(environ)
    return [str(name) for name in stage.get("required_live_env", []) if not env.get(str(name))]


def _stage_decision(stage: dict[str, Any], config: dict[str, Any], environ: dict[str, str] | None = None) -> tuple[str, list[str], bool]:
    live_requested = _live_requested(stage, config, environ)
    missing = _missing_env(stage, environ)
    if not live_requested:
        return "dry_run_ready", [], False
    if not stage.get("live_enabled"):
        return "blocked_live_not_enabled", missing, True
    if missing:
        return "blocked_missing_env", missing, True
    return "live_ready", [], True


def _import_script_run(script_name: str):
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    module = __import__(script_name)
    return module.run


def _run_existing_script(stage: dict[str, Any], script_name: str, environ: dict[str, str] | None) -> dict[str, Any]:
    runner = _import_script_run(script_name)
    result = runner(ROOT / str(stage["config"]), environ=environ)
    return {
        "ok": bool(result.get("ok")),
        "decision": result.get("decision", "unknown"),
        "report": _redact(result),
    }


def _run_graph_memory_export(stage: dict[str, Any], decision: str) -> dict[str, Any]:
    if decision != "live_ready":
        return {"ok": True, "decision": "planned_dry_run", "written": []}
    result = subprocess.run(
        [
            sys.executable,
            "tools/knowledge/graph_memory_export.py",
            "--repo-root",
            ".",
            "--out",
            "knowledge/graph-memory",
        ],
        cwd=ROOT.parents[1],
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "ok": result.returncode == 0,
        "decision": "graph_memory_exported" if result.returncode == 0 else "graph_memory_export_failed",
        "stdout_hash": _digest(result.stdout[-1000:]),
        "stderr_hash": _digest(result.stderr[-1000:]),
    }


def _send_alert(stage: dict[str, Any], decision: str, environ: dict[str, str] | None) -> dict[str, Any]:
    if decision != "live_ready":
        return {"ok": True, "decision": "alert_planned_dry_run", "sent": False}
    webhook = _env(environ).get("VELOCE_ALERT_WEBHOOK", "")
    payload = {
        "text": f"Veloce {stage['id']} live alert pilot fired.",
        "stage": stage["id"],
        "capability": stage["capability"],
        "checked_at": _checked_at(),
        "secret_free": True,
    }
    request = urllib.request.Request(
        webhook,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return {"ok": 200 <= response.status < 300, "decision": "alert_sent", "sent": True, "status": response.status}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "decision": "alert_failed", "sent": False, "status": exc.code}
    except Exception as exc:  # pragma: no cover - defensive network boundary
        return {"ok": False, "decision": "alert_failed", "sent": False, "error": type(exc).__name__}


def _health_gate(stage: dict[str, Any], decision: str) -> dict[str, Any]:
    checks = ["stack_status", "repo_status", "knowledge_graph_status", "github_environment_protection"]
    return {
        "ok": True,
        "decision": "canary_health_gate_live_ready" if decision == "live_ready" else "canary_health_gate_dry_run",
        "production_mutation_performed": False,
        "checks": [{"name": item, "status": "planned" if decision != "live_ready" else "required"} for item in checks],
        "rollback_required": False,
    }


def _rollback_gate(stage: dict[str, Any], decision: str) -> dict[str, Any]:
    return {
        "ok": True,
        "decision": "rollback_execution_live_ready" if decision == "live_ready" else "rollback_execution_dry_run",
        "production_rollback_performed": False,
        "last_known_good_required": True,
        "post_health_required": True,
    }


def _run_adapter(stage: dict[str, Any], decision: str, environ: dict[str, str] | None) -> dict[str, Any]:
    adapter_id = str(stage.get("adapter_id", ""))
    if adapter_id == "graph_memory_export":
        return _run_graph_memory_export(stage, decision)
    if adapter_id == "alert_webhook":
        return _send_alert(stage, decision, environ)
    if adapter_id == "canary_health_gate":
        return _health_gate(stage, decision)
    if adapter_id == "rollback_drill":
        return _rollback_gate(stage, decision)
    return {"ok": False, "decision": "blocked_unknown_adapter", "adapter_id": adapter_id}


def _stage_result(stage: dict[str, Any], config: dict[str, Any], environ: dict[str, str] | None) -> dict[str, Any]:
    checked_at = _checked_at()
    decision, missing, live_requested = _stage_decision(stage, config, environ)
    if stage["capability"] == "paperclip_writeback":
        adapter = _run_existing_script(stage, "paperclip_writeback_proof", environ)
    elif stage["capability"] == "chat_to_pr":
        adapter = _run_existing_script(stage, "chat_to_pr_proof", environ)
    else:
        adapter = _run_adapter(stage, decision, environ)
    ok = decision == "dry_run_ready" or (decision == "live_ready" and adapter.get("ok"))
    return {
        "id": stage["id"],
        "title": stage.get("title", stage["id"]),
        "capability": stage["capability"],
        "checked_at": checked_at,
        "live_requested": live_requested,
        "live_enabled": bool(stage.get("live_enabled")),
        "decision": decision,
        "missing_env": missing,
        "ok": ok,
        "adapter": _redact(adapter),
        "rollback": stage.get("rollback", ""),
        "secret_free": True,
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# V2.6-V3.1 Production AI OS Pilot Pack",
        "",
        f"Checked at: `{report['checked_at']}`",
        f"Status: `{report['status']}`",
        f"Mode: `{report['mode']}`",
        "",
        "| Stage | Capability | Decision | OK |",
        "|---|---|---|---|",
    ]
    for stage in report["stages"]:
        lines.append(f"| `{stage['id']}` | `{stage['capability']}` | `{stage['decision']}` | `{stage['ok']}` |")
    lines.extend(["", "## Safety", "", "Live mutation remains disabled unless both the global live flag and the stage-specific live flag are present, `live_enabled=true`, and scoped env vars are available.", ""])
    return "\n".join(lines)


def _memory_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# V2.6-V3.1 Production AI OS Pilot Pack",
        "",
        f"- Time: {report['checked_at']}",
        f"- Status: {report['status']}",
        f"- Mode: {report['mode']}",
        f"- Audit ledger: {report['audit_ledger']}",
        "",
        "## Stages",
        "",
    ]
    lines.extend(f"- `{stage['id']}`: {stage['decision']}" for stage in report["stages"])
    lines.extend(["", "## Graph Sink", "", "OpenWebUI -> MCPO -> V2.6-V3.1 pilot pack -> audit ledger -> Obsidian/Graphify memory.", ""])
    return "\n".join(lines)


def run(config_path: Path, environ: dict[str, str] | None = None) -> dict[str, Any]:
    config = _load(config_path)
    checked_at = _checked_at()
    stages = [_stage_result(stage, config, environ) for stage in config.get("stages", [])]
    ok = all(stage["ok"] for stage in stages)
    report = {
        "ok": ok,
        "status": "pass" if ok else "blocked",
        "checked_at": checked_at,
        "config": str(config_path),
        "mode": config.get("mode", "dry_run"),
        "issue_id": config.get("issue_id", ""),
        "actor": config.get("actor", ""),
        "stages": stages,
        "audit_ledger": str(config["audit_ledger"]),
        "memory_markdown": str(config["memory_markdown"]),
        "next_action": "Enable one live stage at a time, starting with V2.6 Paperclip writeback.",
        "secret_free": True,
    }
    for key, content in [
        ("generated_json", json.dumps(report, indent=2) + "\n"),
        ("generated_markdown", _markdown(report)),
        ("memory_markdown", _memory_markdown(report)),
    ]:
        path = ROOT / str(config[key])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    audit_path = ROOT / str(config["audit_ledger"])
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as fh:
        for stage in stages:
            fh.write(json.dumps({"checked_at": checked_at, **_redact(stage)}, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V2.6-V3.1 production AI OS pilot pack.")
    parser.add_argument("--config", default="configs/production_ai_os_v2_6_v3_1.json")
    args = parser.parse_args()
    report = run(ROOT / args.config)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
