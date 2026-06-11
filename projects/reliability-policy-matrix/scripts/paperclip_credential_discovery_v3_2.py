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
import uuid


ROOT = Path(__file__).resolve().parents[1]


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


def _env(environ: dict[str, str] | None = None) -> dict[str, str]:
    return environ if environ is not None else os.environ


def _endpoint(base_url: str, template: str, issue_id: str) -> str:
    return f"{base_url.rstrip('/')}{template.format(issue_id=issue_id)}"


def _candidate_base_urls(config: dict[str, Any], environ: dict[str, str] | None = None) -> list[str]:
    env = _env(environ)
    env_base = env.get(str(config.get("paperclip_base_url_env", "PAPERCLIP_BASE_URL")), "").rstrip("/")
    candidates = [str(item).rstrip("/") for item in config.get("candidate_base_urls", []) if str(item).strip()]
    if env_base:
        candidates.insert(0, env_base)
    deduped: list[str] = []
    for item in candidates:
        if item and item not in deduped:
            deduped.append(item)
    return deduped


def _probe_url(url: str, timeout: int = 12) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(200).decode("utf-8", errors="replace")
            return {
                "status": response.status,
                "content_type": response.headers.get("content-type", ""),
                "body_hash": _digest(body),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read(200).decode("utf-8", errors="replace")
        return {
            "status": exc.code,
            "content_type": exc.headers.get("content-type", ""),
            "body_hash": _digest(body),
            "error": "HTTPError",
        }
    except Exception as exc:  # pragma: no cover - network boundary
        return {"status": None, "content_type": "", "body_hash": None, "error": type(exc).__name__}


def _content_kind(content_type: str) -> str:
    normalized = content_type.lower()
    if "json" in normalized:
        return "json_api"
    if "html" in normalized:
        return "frontend_html"
    return "unknown"


def _probe_candidates(config: dict[str, Any], environ: dict[str, str] | None = None) -> list[dict[str, Any]]:
    issue_id = str(config.get("issue_id", "VEL-v2.0F-PILOT"))
    template = str(config.get("issue_get_endpoint_template", "/api/issues/{issue_id}"))
    possible_statuses = {int(item) for item in config.get("possible_api_statuses", [200, 401, 403, 405])}
    probes = []
    for base_url in _candidate_base_urls(config, environ):
        url = _endpoint(base_url, template, issue_id)
        result = _probe_url(url)
        status = result.get("status")
        content_type = str(result.get("content_type", ""))
        kind = _content_kind(content_type)
        api_like = kind == "json_api" or status in {401, 403, 405}
        probes.append(
            {
                "base_url": base_url,
                "url": url,
                "status": status,
                "content_type": content_type,
                "content_kind": kind,
                "body_hash": result.get("body_hash"),
                "error": result.get("error"),
                "api_base_confirmed": bool(api_like),
                "issue_found": bool(api_like and status == 200),
                "issue_missing": bool(api_like and status == 404),
                "possible_api_route": bool(api_like and isinstance(status, int) and status in possible_statuses),
            }
        )
    return probes


def _vps_readonly_commands(config: dict[str, Any]) -> list[str]:
    container = str(config.get("paperclip_container_hint", "paperclip-iraj-paperclip-1"))
    return [
        "docker ps --format 'table {{.Names}}\\t{{.Image}}\\t{{.Status}}' | grep -i paperclip || true",
        f"docker inspect {container} --format '{{{{range .Config.Env}}}}{{{{println .}}}}{{{{end}}}}' | sed 's/=.*//' | sort",
        f"docker exec {container} sh -lc 'printf \"PWD=\"; pwd; echo; echo ROOTS; ls -la / | sed -n \"1,120p\"'",
        f"docker exec {container} sh -lc 'find / -path \"*/.codex/*\" -prune -o -maxdepth 6 -type f \\( -name \"package.json\" -o -name \"routes.*\" -o -name \"schema.prisma\" -o -name \"*.db\" -o -name \"*.sqlite\" -o -name \"*.sqlite3\" \\) -print 2>/dev/null | sort | sed -n \"1,220p\"'",
        f"docker exec {container} sh -lc 'find / -path \"*/.codex/*\" -prune -o -type f \\( -name \"*.js\" -o -name \"*.mjs\" -o -name \"*.ts\" -o -name \"*.tsx\" -o -name \"*.json\" -o -name \"*.py\" \\) -print 2>/dev/null | xargs grep -n \"api/issues\\|comments\\|disposition\\|automation.*token\\|api.*token\\|Bearer\\|Authorization\" 2>/dev/null | sed -n \"1,240p\"'",
    ]


def _decision(probes: list[dict[str, Any]], token_present: bool) -> str:
    if any(item.get("possible_api_route") for item in probes) and token_present:
        return "base_route_candidate_found_token_present"
    if any(item.get("possible_api_route") for item in probes):
        return "base_route_candidate_found_token_missing"
    if any(item.get("issue_missing") for item in probes) and token_present:
        return "api_base_found_pilot_issue_missing_token_present"
    if any(item.get("issue_missing") for item in probes):
        return "api_base_found_pilot_issue_missing_token_missing"
    if any(item.get("content_kind") == "frontend_html" for item in probes):
        return "frontend_routes_only"
    return "base_route_unconfirmed"


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# V3.2 Paperclip Credential Discovery",
        "",
        f"Checked at: `{report['checked_at']}`",
        f"Trace ID: `{report['trace_id']}`",
        f"Decision: `{report['decision']}`",
        f"Token present: `{report['token_present']}`",
        "",
        "## Read-Only Route Probes",
        "",
    ]
    for probe in report["route_probes"]:
        lines.append(
            f"- `{probe['base_url']}` -> status `{probe['status']}`, kind `{probe['content_kind']}`, "
            f"API base confirmed: `{probe['api_base_confirmed']}`, issue found: `{probe['issue_found']}`, "
            f"issue missing: `{probe['issue_missing']}`"
        )
    lines.extend(
        [
            "",
            "## VPS Read-Only Inspection",
            "",
            "Run these only to inspect Paperclip routes/env/schema. They do not create tokens or mutate Paperclip.",
            "",
            "```bash",
            *report["vps_readonly_commands"],
            "```",
            "",
            "## Next Action",
            "",
            report["next_action"],
            "",
        ]
    )
    return "\n".join(lines)


def run(config_path: Path, environ: dict[str, str] | None = None) -> dict[str, Any]:
    config = _load(config_path)
    checked_at = _checked_at()
    trace_id = str(uuid.uuid4())
    env = _env(environ)
    token_name = str(config.get("paperclip_token_env", "PAPERCLIP_AUTOMATION_TOKEN"))
    token_present = bool(env.get(token_name, ""))
    probes = _probe_candidates(config, environ)
    decision = _decision(probes, token_present)
    likely = next((item["base_url"] for item in probes if item.get("possible_api_route")), None)
    if likely is None:
        likely = next((item["base_url"] for item in probes if item.get("api_base_confirmed")), None)
    pilot_issue_missing = any(item.get("issue_missing") for item in probes)
    if pilot_issue_missing:
        next_action = (
            "Create or confirm the exact Paperclip pilot issue VEL-v2.0F-PILOT through the UI/API, then provision a "
            "native scoped PAPERCLIP_AUTOMATION_TOKEN before live writeback."
        )
    elif token_present and likely:
        next_action = "Store PAPERCLIP_BASE_URL and PAPERCLIP_AUTOMATION_TOKEN on the VPS, then run the gated V3.2 live wrapper."
    else:
        next_action = "Inspect the Paperclip backend for a native scoped automation-token mechanism; if absent, add one before live writeback."
    status = "pass" if token_present and any(item.get("possible_api_route") for item in probes) else "needs_inspection"
    report = {
        "ok": True,
        "status": status,
        "service": "paperclip_credential_discovery_v3_2",
        "checked_at": checked_at,
        "trace_id": trace_id,
        "config": str(config_path),
        "mode": config.get("mode", "read_only"),
        "decision": decision,
        "issue_id": str(config.get("issue_id", "")),
        "likely_base_url": likely,
        "pilot_issue_missing": pilot_issue_missing,
        "token_env": token_name,
        "token_present": token_present,
        "token_value_printed": False,
        "route_probes": probes,
        "vps_readonly_commands": _vps_readonly_commands(config),
        "next_action": next_action,
        "secret_free": True,
    }
    ledger = {
        "checked_at": checked_at,
        "trace_id": trace_id,
        "capability": "paperclip_credential_discovery",
        "decision": decision,
        "input_hash": _digest({"issue_id": report["issue_id"], "candidates": _candidate_base_urls(config, environ)}),
        "output_hash": _digest(report),
        "secret_free": True,
    }
    for key, content in [
        ("generated_json", json.dumps(report, indent=2, sort_keys=True) + "\n"),
        ("generated_markdown", _markdown(report)),
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
    parser = argparse.ArgumentParser(description="Read-only Paperclip V3.2 credential and API route discovery.")
    parser.add_argument("--config", default="configs/paperclip_credential_discovery_v3_2.json")
    args = parser.parse_args()
    report = run(ROOT / args.config)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
