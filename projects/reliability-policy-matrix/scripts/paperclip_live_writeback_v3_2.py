from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
import urllib.error
import urllib.request
import uuid

import paperclip_writeback_proof


ROOT = Path(__file__).resolve().parents[1]
PAPERCLIP_ISSUE_ID_RE = re.compile(r"^VEL-(?:v2\.0F-PILOT|[0-9]+)$")
SECRET_KEY_PARTS = ("authorization", "api_key", "apikey", "password")
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


def _is_secret_key(key: str) -> bool:
    normalized = key.lower()
    if normalized in {"token", "secret", "authorization"}:
        return True
    return any(part in normalized for part in SECRET_KEY_PARTS) or normalized.endswith(SECRET_KEY_SUFFIXES)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[redacted]" if _is_secret_key(key) else _redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _env(environ: dict[str, str] | None = None) -> dict[str, str]:
    return environ if environ is not None else os.environ


def _live_requested(config: dict[str, Any], environ: dict[str, str] | None = None) -> bool:
    env = _env(environ)
    global_requested = env.get(str(config.get("global_live_enable_env"))) == str(
        config.get("global_live_enable_value", "1")
    )
    stage_requested = env.get(str(config.get("live_enable_env"))) == str(config.get("live_enable_value", "1"))
    return global_requested and stage_requested


def _paperclip_env(config: dict[str, Any], environ: dict[str, str] | None = None) -> tuple[str, str, list[str]]:
    env = _env(environ)
    base_name = str(config.get("paperclip_base_url_env", "PAPERCLIP_BASE_URL"))
    token_name = str(config.get("paperclip_token_env", "PAPERCLIP_AUTOMATION_TOKEN"))
    base_url = env.get(base_name, "").rstrip("/")
    token = env.get(token_name, "")
    missing = [name for name, value in [(base_name, base_url), (token_name, token)] if not value]
    return base_url, token, missing


def _target_issue(config: dict[str, Any], environ: dict[str, str] | None = None) -> tuple[str, str, str, bool]:
    env = _env(environ)
    env_name = str(config.get("paperclip_pilot_issue_id_env", "PAPERCLIP_PILOT_ISSUE_ID"))
    env_value = env.get(env_name, "").strip()
    issue_id = env_value or str(config.get("issue_id", "")).strip()
    required_issue_id = env_value or str(config.get("required_issue_id", "VEL-v2.0F-PILOT")).strip()
    source = "env" if env_value else "config"
    valid_format = bool(PAPERCLIP_ISSUE_ID_RE.match(issue_id)) and bool(PAPERCLIP_ISSUE_ID_RE.match(required_issue_id))
    return issue_id, required_issue_id, source, valid_format


def _endpoint(base_url: str, template: str, issue_id: str) -> str:
    return f"{base_url}{template.format(issue_id=issue_id)}"


def _request_json(
    url: str,
    method: str,
    token: str,
    payload: dict[str, Any] | None,
    allowed_statuses: set[int],
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            parsed: Any
            try:
                parsed = json.loads(body) if body else {}
            except json.JSONDecodeError:
                parsed = {}
            return {
                "ok": response.status in allowed_statuses,
                "status": response.status,
                "body_hash": _digest(body[:1000]),
                "json": parsed if isinstance(parsed, dict) else {},
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "status": exc.code, "error": "HTTPError", "body_hash": _digest(body[:1000]), "json": {}}
    except Exception as exc:  # pragma: no cover - defensive network boundary
        return {"ok": False, "status": None, "error": type(exc).__name__, "json": {}}


def _preflight_decision(config: dict[str, Any], environ: dict[str, str] | None) -> tuple[str, list[str], bool]:
    issue_id, required_issue_id, _, valid_issue_format = _target_issue(config, environ)
    if not valid_issue_format:
        return "blocked_invalid_paperclip_issue_id", [], False
    if issue_id != required_issue_id:
        return "blocked_wrong_issue_id", [], False
    live_requested = _live_requested(config, environ)
    if not live_requested:
        return "dry_run_ready", [], False
    if not config.get("live_enabled"):
        return "blocked_live_not_enabled", [], True
    _, _, missing = _paperclip_env(config, environ)
    if missing:
        return "blocked_missing_env", missing, True
    return "live_ready", [], True


def _previous_issue_state(config: dict[str, Any], environ: dict[str, str] | None, decision: str) -> dict[str, Any]:
    if decision != "live_ready":
        return {"decision": "not_checked_dry_run", "previous_disposition": None}
    base_url, token, _ = _paperclip_env(config, environ)
    issue_id, _, _, _ = _target_issue(config, environ)
    allowed_statuses = {int(item) for item in config.get("allowed_statuses", [200, 201, 204])}
    result = _request_json(
        _endpoint(base_url, str(config.get("issue_get_endpoint_template", "/api/issues/{issue_id}")), issue_id),
        "GET",
        token,
        None,
        allowed_statuses,
    )
    body = result.get("json", {})
    previous_disposition = None
    if isinstance(body, dict):
        previous_disposition = body.get("disposition") or body.get("status")
    return {
        "decision": "checked" if result.get("ok") else "unavailable",
        "ok": bool(result.get("ok")),
        "status": result.get("status"),
        "previous_disposition": previous_disposition,
        "body_hash": result.get("body_hash"),
    }


def _effective_config(config: dict[str, Any], trace_id: str, environ: dict[str, str] | None = None) -> dict[str, Any]:
    base_path = ROOT / str(config.get("base_config", "configs/paperclip_writeback_v2_0F.json"))
    effective = _load(base_path)
    issue_id, _, _, _ = _target_issue(config, environ)
    comment = str(config.get("comment_markdown", effective.get("comment_markdown", ""))).rstrip()
    comment = comment.replace(str(config.get("issue_id", "VEL-v2.0F-PILOT")), issue_id)
    marker = str(config.get("idempotency_marker", "V3.2 Paperclip live pilot"))
    if marker not in comment:
        comment = f"{marker}\n\n{comment}"
    comment = f"{comment}\n\nTrace ID: {trace_id}"
    effective.update(
        {
            "generated_json": str(config["generated_json"]),
            "generated_markdown": str(config["generated_markdown"]),
            "audit_ledger": str(config["audit_ledger"]),
            "memory_markdown": str(config["memory_markdown"]),
            "mode": config.get("mode", "dry_run"),
            "proof_title": config.get("proof_title", "V3.2 Paperclip Live Writeback"),
            "action_id": config.get("action_id", "v3.2-paperclip-live-writeback"),
            "issue_id": issue_id,
            "actor": config.get("actor", ""),
            "live_enable_env": config.get("live_enable_env", "VELOCE_PAPERCLIP_WRITEBACK_LIVE"),
            "live_enable_value": config.get("live_enable_value", "1"),
            "live_enabled": bool(config.get("live_enabled")),
            "paperclip_base_url_env": config.get("paperclip_base_url_env", "PAPERCLIP_BASE_URL"),
            "paperclip_token_env": config.get("paperclip_token_env", "PAPERCLIP_AUTOMATION_TOKEN"),
            "comment_endpoint_template": config.get("comment_endpoint_template", effective.get("comment_endpoint_template")),
            "disposition_endpoint_template": config.get(
                "disposition_endpoint_template", effective.get("disposition_endpoint_template")
            ),
            "target_disposition": config.get("target_disposition", effective.get("target_disposition", "in_review")),
            "rollback_disposition": config.get("rollback_disposition", effective.get("rollback_disposition", "in_review")),
            "allowed_statuses": config.get("allowed_statuses", effective.get("allowed_statuses", [200, 201, 204])),
            "comment_markdown": comment,
        }
    )
    return effective


def _write_effective_config(config: dict[str, Any], effective: dict[str, Any]) -> Path:
    path = ROOT / str(config.get("effective_paperclip_config", "artifacts/derived/paperclip_writeback_v3_2_effective.local.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(effective, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_local_live_config(config: dict[str, Any], environ: dict[str, str] | None = None) -> Path:
    path = ROOT / str(config["local_live_config"])
    local = dict(config)
    issue_id, required_issue_id, _, _ = _target_issue(config, environ)
    local["issue_id"] = issue_id
    local["required_issue_id"] = required_issue_id
    local["live_enabled"] = True
    local["mode"] = "live_candidate"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(local, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _rollback_packet(
    config: dict[str, Any],
    trace_id: str,
    proof_report: dict[str, Any],
    previous: dict[str, Any],
    restore_result: dict[str, Any] | None,
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    comment_ok = bool(proof_report.get("comment_result", {}).get("ok"))
    disposition_ok = bool(proof_report.get("disposition_result", {}).get("ok"))
    partial_failure = proof_report.get("decision") == "live_ready" and comment_ok != disposition_ok
    return {
        "trace_id": trace_id,
        "issue_id": _target_issue(config, environ)[0],
        "decision": "rollback_packet_ready" if partial_failure else "rollback_not_required",
        "partial_failure": partial_failure,
        "previous_disposition": previous.get("previous_disposition"),
        "restore_attempted": restore_result is not None,
        "restore_result": _redact(restore_result or {}),
        "correction_comment": "Post a correction comment and restore prior disposition when a partial live write occurs.",
        "secret_free": True,
    }


def _restore_previous_disposition(
    config: dict[str, Any],
    environ: dict[str, str] | None,
    previous: dict[str, Any],
    proof_report: dict[str, Any],
) -> dict[str, Any] | None:
    comment_ok = bool(proof_report.get("comment_result", {}).get("ok"))
    disposition_ok = bool(proof_report.get("disposition_result", {}).get("ok"))
    previous_disposition = previous.get("previous_disposition")
    if not config.get("restore_on_partial_failure", True) or comment_ok == disposition_ok or not previous_disposition:
        return None
    base_url, token, _ = _paperclip_env(config, environ)
    issue_id, _, _, _ = _target_issue(config, environ)
    allowed_statuses = {int(item) for item in config.get("allowed_statuses", [200, 201, 204])}
    payload = {"disposition": previous_disposition}
    return _request_json(
        _endpoint(base_url, str(config.get("disposition_endpoint_template", "/api/issues/{issue_id}")), issue_id),
        "PATCH",
        token,
        payload,
        allowed_statuses,
    )


def _markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# V3.2 Paperclip Live Writeback",
            "",
            f"Checked at: `{report['checked_at']}`",
            f"Trace ID: `{report['trace_id']}`",
            f"Decision: `{report['decision']}`",
            f"Issue: `{report['issue_id']}`",
            f"Live requested: `{report['live_requested']}`",
            "",
            "## Results",
            "",
            f"- Preflight: `{report['preflight']['decision']}`",
            f"- Comment: `{report['comment_result']['decision']}`",
            f"- Disposition: `{report['disposition_result']['decision']}`",
            f"- Rollback packet: `{report['rollback_packet']['decision']}`",
            "",
        ]
    )


def _memory_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# V3.2 Paperclip Live Writeback",
            "",
            f"- Time: {report['checked_at']}",
            f"- Trace ID: {report['trace_id']}",
            f"- Issue: {report['issue_id']}",
            f"- Decision: {report['decision']}",
            f"- Audit ledger: {report['audit_ledger']}",
            "",
            "## Scope",
            "",
            "One scoped Paperclip issue comment and one scoped disposition update.",
            "",
            "## Graph Sink",
            "",
            "Paperclip live writeback -> audit JSONL -> Obsidian/Graphify memory -> OpenWebUI knowledge graph query.",
            "",
        ]
    )


def run(config_path: Path, environ: dict[str, str] | None = None) -> dict[str, Any]:
    config = _load(config_path)
    trace_id = str(uuid.uuid4())
    checked_at = _checked_at()
    issue_id, required_issue_id, issue_id_source, issue_id_valid = _target_issue(config, environ)
    decision, missing_env, live_requested = _preflight_decision(config, environ)
    effective = _effective_config(config, trace_id, environ)
    local_live_config = _write_local_live_config(config, environ)
    effective_config = _write_effective_config(config, effective)
    previous = _previous_issue_state(config, environ, decision)

    if decision in {"dry_run_ready", "live_ready"}:
        proof_report = paperclip_writeback_proof.run(effective_config, environ=environ)
    else:
        proof_report = {
            "ok": False,
            "decision": decision,
            "comment_result": {"decision": "blocked"},
            "disposition_result": {"decision": "blocked"},
        }

    restore_result = _restore_previous_disposition(config, environ, previous, proof_report) if decision == "live_ready" else None
    rollback = _rollback_packet(config, trace_id, proof_report, previous, restore_result, environ)
    ok = decision == "dry_run_ready" or (decision == "live_ready" and proof_report.get("ok"))
    report = {
        "ok": ok,
        "status": "pass" if ok else "blocked",
        "checked_at": checked_at,
        "trace_id": trace_id,
        "config": str(config_path),
        "local_live_config": str(local_live_config),
        "effective_paperclip_config": str(effective_config),
        "issue_id": issue_id,
        "required_issue_id": required_issue_id,
        "issue_id_source": issue_id_source,
        "issue_id_valid": issue_id_valid,
        "live_requested": live_requested,
        "live_enabled": bool(config.get("live_enabled")),
        "decision": proof_report.get("decision", decision) if decision in {"dry_run_ready", "live_ready"} else decision,
        "missing_env": missing_env,
        "preflight": {
            "decision": decision,
            "env_present": not missing_env,
            "issue_locked": issue_id_valid and issue_id == required_issue_id,
            "previous_issue_state": _redact(previous),
        },
        "comment_result": _redact(proof_report.get("comment_result", {})),
        "disposition_result": _redact(proof_report.get("disposition_result", {})),
        "rollback_packet": rollback,
        "audit_ledger": str(config["audit_ledger"]),
        "memory_markdown": str(config["memory_markdown"]),
        "secret_free": True,
    }
    ledger = {
        "action_id": config.get("action_id", "v3.2-paperclip-live-writeback"),
        "checked_at": checked_at,
        "trace_id": trace_id,
        "issue_id": issue_id,
        "capability": "paperclip_writeback",
        "decision": report["decision"],
        "input_hash": _digest({"issue_id": issue_id, "marker": config.get("idempotency_marker")}),
        "output_hash": _digest(_redact(report)),
        "rollback_packet": rollback["decision"],
        "secret_free": True,
    }
    for key, content in [
        ("generated_json", json.dumps(report, indent=2, sort_keys=True) + "\n"),
        ("generated_markdown", _markdown(report)),
        ("memory_markdown", _memory_markdown(report)),
        ("rollback_packet", json.dumps(rollback, indent=2, sort_keys=True) + "\n"),
    ]:
        path = ROOT / str(config[key])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    audit_path = ROOT / str(config["audit_ledger"])
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ledger, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V3.2 Paperclip live writeback wrapper.")
    parser.add_argument("--config", default="configs/paperclip_writeback_v3_2.json")
    args = parser.parse_args()
    report = run(ROOT / args.config)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
