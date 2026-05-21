from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any
import urllib.error
import urllib.request


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


def _is_live_requested(config: dict[str, Any], environ: dict[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return env.get(str(config.get("live_enable_env", "VELOCE_PAPERCLIP_WRITEBACK_LIVE"))) == str(
        config.get("live_enable_value", "1")
    )


def _paperclip_env(config: dict[str, Any], environ: dict[str, str] | None = None) -> tuple[str, str, list[str]]:
    env = environ if environ is not None else os.environ
    base_name = str(config.get("paperclip_base_url_env", "PAPERCLIP_BASE_URL"))
    token_name = str(config.get("paperclip_token_env", "PAPERCLIP_AUTOMATION_TOKEN"))
    base_url = env.get(base_name, "").rstrip("/")
    token = env.get(token_name, "")
    missing = [name for name, value in [(base_name, base_url), (token_name, token)] if not value]
    return base_url, token, missing


def _endpoint(base_url: str, template: str, issue_id: str) -> str:
    return f"{base_url}{template.format(issue_id=issue_id)}"


def _request_json(
    url: str,
    method: str,
    token: str,
    payload: dict[str, Any],
    allowed_statuses: set[int],
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
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
            return {
                "ok": response.status in allowed_statuses,
                "status": response.status,
                "body_hash": _digest(body[:1000]),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": exc.code,
            "error": "HTTPError",
            "body_hash": _digest(body[:1000]),
        }
    except Exception as exc:  # pragma: no cover - defensive network boundary
        return {"ok": False, "status": None, "error": type(exc).__name__}


def _memory_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# V2.0A Paperclip Scoped Writeback Proof",
            "",
            f"- Time: {report['checked_at']}",
            f"- Issue: {report['issue_id']}",
            f"- Mode: {report['mode']}",
            f"- Decision: {report['decision']}",
            f"- Comment result: {report['comment_result']['decision']}",
            f"- Disposition result: {report['disposition_result']['decision']}",
            f"- Audit ledger: {report['audit_ledger']}",
            "",
            "## Scope",
            "",
            "One scoped Paperclip issue comment and one scoped disposition update.",
            "",
            "## Rollback",
            "",
            report["rollback"],
            "",
        ]
    )


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# V2.0A Paperclip Scoped Writeback Proof",
        "",
        f"Checked at: `{report['checked_at']}`",
        f"Status: `{report['status']}`",
        f"Mode: `{report['mode']}`",
        f"Live requested: `{report['live_requested']}`",
        f"Decision: `{report['decision']}`",
        f"Issue: `{report['issue_id']}`",
        "",
        "## Results",
        "",
        f"- Comment: `{report['comment_result']['decision']}`",
        f"- Disposition: `{report['disposition_result']['decision']}`",
        "",
        "## Audit",
        "",
        f"- `{report['audit_ledger']}`",
        f"- `{report['memory_markdown']}`",
        "",
    ]
    return "\n".join(lines)


def run(config_path: Path, environ: dict[str, str] | None = None) -> dict[str, Any]:
    config = _load(config_path)
    checked_at = _checked_at()
    issue_id = str(config.get("issue_id", ""))
    live_requested = _is_live_requested(config, environ)
    live_enabled = bool(config.get("live_enabled"))
    base_url, token, missing_env = _paperclip_env(config, environ)
    allowed_statuses = {int(item) for item in config.get("allowed_statuses", [200, 201, 204])}
    comment_payload = {str(config.get("comment_field", "body")): str(config.get("comment_markdown", ""))}
    disposition_payload = {
        str(config.get("disposition_field", "disposition")): str(config.get("target_disposition", "in_review"))
    }

    if not live_requested:
        decision = "dry_run_ready"
    elif not live_enabled:
        decision = "blocked_live_not_enabled"
    elif missing_env:
        decision = "blocked_missing_env"
    else:
        decision = "live_ready"

    comment_result = {
        "decision": "not_sent_dry_run" if decision == "dry_run_ready" else "blocked",
        "request": {
            "method": config.get("comment_method", "POST"),
            "endpoint_template": config.get("comment_endpoint_template", ""),
            "payload_hash": _digest(comment_payload),
        },
    }
    disposition_result = {
        "decision": "not_sent_dry_run" if decision == "dry_run_ready" else "blocked",
        "request": {
            "method": config.get("disposition_method", "PATCH"),
            "endpoint_template": config.get("disposition_endpoint_template", ""),
            "payload_hash": _digest(disposition_payload),
        },
    }

    if decision == "live_ready":
        comment_result = {
            "decision": "sent",
            **_request_json(
                _endpoint(base_url, str(config["comment_endpoint_template"]), issue_id),
                str(config.get("comment_method", "POST")),
                token,
                comment_payload,
                allowed_statuses,
            ),
        }
        disposition_result = {
            "decision": "sent",
            **_request_json(
                _endpoint(base_url, str(config["disposition_endpoint_template"]), issue_id),
                str(config.get("disposition_method", "PATCH")),
                token,
                disposition_payload,
                allowed_statuses,
            ),
        }

    ok = decision == "dry_run_ready" or (
        decision == "live_ready" and comment_result.get("ok") and disposition_result.get("ok")
    )
    report = {
        "ok": ok,
        "status": "pass" if ok else "blocked",
        "checked_at": checked_at,
        "config": str(config_path),
        "mode": config.get("mode", "dry_run"),
        "issue_id": issue_id,
        "actor": config.get("actor", ""),
        "live_requested": live_requested,
        "live_enabled": live_enabled,
        "decision": decision,
        "missing_env": missing_env if live_requested else [],
        "comment_result": comment_result,
        "disposition_result": disposition_result,
        "rollback": (
            "Post a correction comment and restore disposition to "
            f"{config.get('rollback_disposition', 'in_review')}."
        ),
        "audit_ledger": str(config["audit_ledger"]),
        "memory_markdown": str(config["memory_markdown"]),
        "secret_free": True,
    }

    ledger = {
        "action_id": "v2.0A-paperclip-writeback",
        "checked_at": checked_at,
        "issue_id": issue_id,
        "actor": config.get("actor", ""),
        "capability": "paperclip_writeback",
        "decision": decision,
        "input_hash": _digest({"issue_id": issue_id, "comment": comment_payload, "disposition": disposition_payload}),
        "output_hash": _digest(_redact(report)),
        "rollback": report["rollback"],
        "secret_free": True,
    }

    for path_key, content in [
        ("generated_json", json.dumps(report, indent=2) + "\n"),
        ("generated_markdown", _markdown(report)),
        ("memory_markdown", _memory_markdown(report)),
    ]:
        path = Path(config[path_key])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    ledger_path = Path(config["audit_ledger"])
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(ledger, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V2.0A Paperclip scoped writeback proof.")
    parser.add_argument("--config", default="configs/paperclip_writeback_v2_0A.json")
    args = parser.parse_args()
    report = run(Path(args.config))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
