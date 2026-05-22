from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request


SECRET_KEYS = {"authorization", "token", "api_key", "password", "secret"}
BRANCH_SAFE = re.compile(r"[^A-Za-z0-9._/-]+")


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
    return env.get(str(config.get("live_enable_env", "VELOCE_CHAT_TO_PR_LIVE"))) == str(
        config.get("live_enable_value", "1")
    )


def _github_env(config: dict[str, Any], environ: dict[str, str] | None = None) -> tuple[str, str, list[str]]:
    env = _env(environ)
    token_name = str(config.get("github_token_env", "GITHUB_TOKEN"))
    repo_name = str(config.get("github_repository_env", "GITHUB_REPOSITORY"))
    token = env.get(token_name, "")
    repo = env.get(repo_name, "")
    missing = [name for name, value in [(token_name, token), (repo_name, repo)] if not value]
    return token, repo, missing


def _safe_branch(config: dict[str, Any], issue_id: str) -> str:
    raw = f"{config.get('branch_prefix', 'veloce/v2.0B-chat-to-pr')}-{issue_id}".strip("-")
    return BRANCH_SAFE.sub("-", raw).strip("/-")[:180]


def _file_allowed(path: str, allowed_prefixes: list[str]) -> bool:
    return bool(path) and not path.startswith("/") and ".." not in Path(path).parts and any(
        path.startswith(prefix) for prefix in allowed_prefixes
    )


def _github_request(
    api_base: str,
    repo: str,
    token: str,
    path: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{api_base.rstrip('/')}/repos/{repo}/{path.lstrip('/')}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "veloce-chat-to-pr-proof",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(body) if body else {}
            return {"ok": 200 <= response.status < 300, "status": response.status, "json": parsed}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"body_hash": _digest(body[:1000])}
        return {"ok": False, "status": exc.code, "error": "HTTPError", "json": parsed}
    except Exception as exc:  # pragma: no cover - defensive network boundary
        return {"ok": False, "status": None, "error": type(exc).__name__, "json": {}}


def _github_live_flow(config: dict[str, Any], token: str, repo: str, branch: str, proof_file: str) -> dict[str, Any]:
    api_base = str(config.get("github_api_base", "https://api.github.com"))
    base_branch = str(config.get("base_branch", "main"))
    proof_markdown = str(config.get("proof_markdown", ""))
    commit_message = str(config.get("commit_message", "docs: add v2.0B chat-to-PR live proof"))

    base_ref = _github_request(api_base, repo, token, f"git/ref/heads/{urllib.parse.quote(base_branch, safe='')}")
    if not base_ref.get("ok"):
        return {"ok": False, "step": "get_base_ref", "result": _redact(base_ref)}

    base_sha = base_ref.get("json", {}).get("object", {}).get("sha", "")
    create_ref = _github_request(
        api_base,
        repo,
        token,
        "git/refs",
        method="POST",
        payload={"ref": f"refs/heads/{branch}", "sha": base_sha},
    )
    if not create_ref.get("ok") and create_ref.get("status") != 422:
        return {"ok": False, "step": "create_branch", "result": _redact(create_ref)}

    encoded_file = urllib.parse.quote(proof_file, safe="/")
    existing = _github_request(api_base, repo, token, f"contents/{encoded_file}?ref={urllib.parse.quote(branch, safe='')}")
    put_payload: dict[str, Any] = {
        "message": commit_message,
        "content": base64.b64encode(proof_markdown.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if existing.get("ok") and existing.get("json", {}).get("sha"):
        put_payload["sha"] = existing["json"]["sha"]

    write_file = _github_request(api_base, repo, token, f"contents/{encoded_file}", method="PUT", payload=put_payload)
    if not write_file.get("ok"):
        return {"ok": False, "step": "write_file", "result": _redact(write_file)}

    create_pr = _github_request(
        api_base,
        repo,
        token,
        "pulls",
        method="POST",
        payload={
            "title": str(config.get("pr_title", "V2.0B Chat-to-PR Proof")),
            "head": branch,
            "base": base_branch,
            "body": str(config.get("pr_body", "")),
            "maintainer_can_modify": True,
        },
    )
    if not create_pr.get("ok") and create_pr.get("status") != 422:
        return {"ok": False, "step": "create_pr", "result": _redact(create_pr)}

    return {
        "ok": True,
        "branch_result": {"status": create_ref.get("status"), "already_exists": create_ref.get("status") == 422},
        "file_result": {
            "status": write_file.get("status"),
            "commit_sha": write_file.get("json", {}).get("commit", {}).get("sha", ""),
        },
        "pr_result": {
            "status": create_pr.get("status"),
            "number": create_pr.get("json", {}).get("number"),
            "url": create_pr.get("json", {}).get("html_url"),
            "already_exists": create_pr.get("status") == 422,
        },
    }


def _memory_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {report['proof_title']}",
            "",
            f"- Time: {report['checked_at']}",
            f"- Issue: {report['issue_id']}",
            f"- Mode: {report['mode']}",
            f"- Decision: {report['decision']}",
            f"- Repository: {report['repository']}",
            f"- Branch: {report['branch']}",
            f"- Proof file: {report['proof_file']}",
            f"- Audit ledger: {report['audit_ledger']}",
            "",
            "## Scope",
            "",
            "Approved chat plan to docs-only GitHub pull request.",
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
            f"# {report['proof_title']}",
            "",
            f"Checked at: `{report['checked_at']}`",
            f"Status: `{report['status']}`",
            f"Mode: `{report['mode']}`",
            f"Live requested: `{report['live_requested']}`",
            f"Decision: `{report['decision']}`",
            f"Repository: `{report['repository']}`",
            f"Branch: `{report['branch']}`",
            f"Proof file: `{report['proof_file']}`",
            "",
            "## Results",
            "",
            f"- Branch: `{report['branch_result']['decision']}`",
            f"- File write: `{report['file_result']['decision']}`",
            f"- Pull request: `{report['pr_result']['decision']}`",
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
    issue_id = str(config.get("issue_id", ""))
    token, repo, missing_env = _github_env(config, environ)
    live_requested = _is_live_requested(config, environ)
    live_enabled = bool(config.get("live_enabled"))
    allowed_prefixes = [str(prefix) for prefix in config.get("allowed_file_prefixes", ["docs/"])]
    proof_file = str(config.get("proof_file", ""))
    branch = _safe_branch(config, issue_id)
    file_allowed = _file_allowed(proof_file, allowed_prefixes)

    if not file_allowed:
        decision = "blocked_disallowed_file"
    elif not live_requested:
        decision = "dry_run_ready"
    elif not live_enabled:
        decision = "blocked_live_not_enabled"
    elif missing_env:
        decision = "blocked_missing_env"
    else:
        decision = "live_ready"

    branch_result = {"decision": "not_sent_dry_run" if decision == "dry_run_ready" else "blocked"}
    file_result = {
        "decision": "not_sent_dry_run" if decision == "dry_run_ready" else "blocked",
        "payload_hash": _digest({"path": proof_file, "content": config.get("proof_markdown", "")}),
    }
    pr_result = {"decision": "not_sent_dry_run" if decision == "dry_run_ready" else "blocked"}

    if decision == "live_ready":
        live_result = _github_live_flow(config, token, repo, branch, proof_file)
        if live_result.get("ok"):
            branch_result = {"decision": "sent", **live_result.get("branch_result", {})}
            file_result = {"decision": "sent", **live_result.get("file_result", {})}
            pr_result = {"decision": "sent", **live_result.get("pr_result", {})}
        else:
            decision = f"blocked_{live_result.get('step', 'github_request')}"
            branch_result = {"decision": "blocked", "detail": live_result.get("step")}
            file_result = {"decision": "blocked", "detail": live_result.get("step")}
            pr_result = {"decision": "blocked", "detail": live_result.get("step")}

    ok = decision == "dry_run_ready" or (
        decision == "live_ready"
        and branch_result.get("decision") == "sent"
        and file_result.get("decision") == "sent"
        and pr_result.get("decision") == "sent"
    )
    report = {
        "ok": ok,
        "status": "pass" if ok else "blocked",
        "checked_at": checked_at,
        "proof_title": str(config.get("proof_title", "V2.0B Chat-to-PR Proof")),
        "config": str(config_path),
        "mode": config.get("mode", "dry_run"),
        "issue_id": issue_id,
        "actor": config.get("actor", ""),
        "repository": repo if repo else "<missing>",
        "base_branch": config.get("base_branch", "main"),
        "branch": branch,
        "proof_file": proof_file,
        "allowed_file_prefixes": allowed_prefixes,
        "file_allowed": file_allowed,
        "live_requested": live_requested,
        "live_enabled": live_enabled,
        "decision": decision,
        "missing_env": missing_env if live_requested else [],
        "branch_result": branch_result,
        "file_result": file_result,
        "pr_result": pr_result,
        "rollback": "Close the generated PR and delete the generated branch.",
        "audit_ledger": str(config["audit_ledger"]),
        "memory_markdown": str(config["memory_markdown"]),
        "secret_free": True,
    }

    ledger = {
        "action_id": str(config.get("action_id", "v2.0B-chat-to-pr")),
        "checked_at": checked_at,
        "issue_id": issue_id,
        "actor": config.get("actor", ""),
        "capability": "chat_to_pr",
        "decision": decision,
        "repository": repo if repo else "<missing>",
        "branch": branch,
        "proof_file": proof_file,
        "input_hash": _digest(
            {
                "issue_id": issue_id,
                "repository": repo if repo else "<missing>",
                "branch": branch,
                "proof_file": proof_file,
                "pr_title": config.get("pr_title", ""),
            }
        ),
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
    parser = argparse.ArgumentParser(description="Run V2.0B chat-to-PR proof.")
    parser.add_argument("--config", default="configs/chat_to_pr_v2_0B.json")
    args = parser.parse_args()
    report = run(Path(args.config))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
