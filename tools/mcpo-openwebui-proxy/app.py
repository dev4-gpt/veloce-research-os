from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse


PORT = int(os.environ.get("PORT", "8080"))
MCPO_BASE_URL = os.environ.get("MCPO_BASE_URL", "http://mcpo-time:8000").rstrip("/")
MCPO_API_KEY = os.environ.get("MCPO_API_KEY", "")
PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    "https://tools.srv1314350.hstgr.cloud",
).rstrip("/")
ALLOWED_ORIGIN = os.environ.get(
    "ALLOWED_ORIGIN",
    "https://chat.srv1314350.hstgr.cloud",
)
OPENWEBUI_URL = os.environ.get("OPENWEBUI_URL", "http://openwebui:8080").rstrip("/")
HERMES_URL = os.environ.get("HERMES_URL", "http://hermes:8642").rstrip("/")
PAPERCLIP_URL = os.environ.get(
    "PAPERCLIP_URL",
    "http://paperclip-iraj-paperclip-1:3100",
).rstrip("/")
RESEARCH_REPO_PATH = Path(
    os.environ.get("RESEARCH_REPO_PATH", "/workspace/veloce-research-os")
)
RUFLO_SANDBOX_PATH = Path(
    os.environ.get("RUFLO_SANDBOX_PATH", "/workspace/ruflo-sandbox")
)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2).encode("utf-8")


def _openapi_spec() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Veloce MCPO Proxy",
            "version": "0.1.0",
            "description": "Open WebUI-compatible proxy for selected Veloce MCPO tools.",
        },
        "servers": [{"url": PUBLIC_BASE_URL}],
        "paths": {
            "/stack_status": {
                "post": {
                    "operationId": "stack_status",
                    "summary": "Check read-only Veloce stack status.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": False,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {},
                                    "additionalProperties": False,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Stack status result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/repo_status": {
                "post": {
                    "operationId": "repo_status",
                    "summary": "Check read-only Veloce research repository status.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": False,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {},
                                    "additionalProperties": False,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Repository status result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/ruflo_status": {
                "post": {
                    "operationId": "ruflo_status",
                    "summary": "Check read-only Ruflo sandbox status.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": False,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "scope": {
                                            "type": "string",
                                            "default": "sandbox",
                                            "enum": ["sandbox"],
                                        }
                                    },
                                    "additionalProperties": False,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Ruflo sandbox status result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/ruflo_plan": {
                "post": {
                    "operationId": "ruflo_plan",
                    "summary": "Create a planning-only Ruflo bridge plan for a Paperclip issue.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "issue_id": {"type": "string"},
                                        "title": {"type": "string"},
                                        "description": {"type": "string"},
                                        "priority": {"type": "string", "default": "medium"},
                                        "assignee": {
                                            "type": "string",
                                            "default": "Technical Builder",
                                        },
                                        "labels": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "requested_mode": {
                                            "type": "string",
                                            "default": "plan",
                                        },
                                    },
                                    "required": ["title", "description"],
                                    "additionalProperties": True,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Planning-only bridge result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/get_current_time": {
                "post": {
                    "operationId": "get_current_time",
                    "summary": "Get current time for a timezone.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "timezone": {
                                            "type": "string",
                                            "default": "America/New_York",
                                        }
                                    },
                                    "required": ["timezone"],
                                    "additionalProperties": False,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Time result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                        "502": {"description": "MCPO upstream error"},
                    },
                }
            },
            "/convert_time": {
                "post": {
                    "operationId": "convert_time",
                    "summary": "Convert time between timezones.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "source_timezone": {"type": "string"},
                                        "target_timezone": {"type": "string"},
                                        "time": {"type": "string"},
                                    },
                                    "required": [
                                        "source_timezone",
                                        "target_timezone",
                                        "time",
                                    ],
                                    "additionalProperties": False,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Converted time result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                        "502": {"description": "MCPO upstream error"},
                    },
                }
            },
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                }
            }
        },
    }


def _http_probe(name: str, url: str, timeout: float = 3.0) -> dict[str, Any]:
    started = time.time()
    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(300).decode("utf-8", errors="replace")
            return {
                "ok": 200 <= response.status < 400,
                "status": response.status,
                "latency_ms": int((time.time() - started) * 1000),
                "detail": body,
            }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "latency_ms": int((time.time() - started) * 1000),
            "detail": f"{name} check failed: {type(exc).__name__}: {exc}",
        }


def _tcp_probe(name: str, url: str, timeout: float = 1.0) -> dict[str, Any]:
    started = time.time()
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            raise ValueError(f"missing host in {url}")
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=timeout):
            return {
                "ok": True,
                "status": "tcp_open",
                "latency_ms": int((time.time() - started) * 1000),
                "detail": f"TCP connection to {host}:{port} succeeded",
            }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "latency_ms": int((time.time() - started) * 1000),
            "detail": f"{name} check failed: {type(exc).__name__}: {exc}",
        }


def _read_git_commit(repo_path: Path) -> dict[str, Any]:
    git_dir = repo_path / ".git"
    head_path = git_dir / "HEAD"
    if not head_path.exists():
        return {
            "ok": False,
            "path": str(repo_path),
            "detail": "repo .git/HEAD not found; mount the repo read-only",
        }

    head = head_path.read_text(encoding="utf-8").strip()
    branch = None
    commit = None

    if head.startswith("ref: "):
        ref = head.removeprefix("ref: ").strip()
        branch = ref.removeprefix("refs/heads/")
        ref_path = git_dir / ref
        if ref_path.exists():
            commit = ref_path.read_text(encoding="utf-8").strip()
        else:
            packed_refs = git_dir / "packed-refs"
            if packed_refs.exists():
                for line in packed_refs.read_text(encoding="utf-8").splitlines():
                    if line and not line.startswith("#") and line.endswith(f" {ref}"):
                        commit = line.split(" ", 1)[0]
                        break
    else:
        commit = head

    return {
        "ok": bool(commit),
        "path": str(repo_path),
        "branch": branch,
        "commit": commit,
        "detail": "read-only git metadata",
    }


def _run_git(repo_path: Path, args: list[str], timeout: float = 3.0) -> str:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=True,
        capture_output=True,
        env=env,
        text=True,
        timeout=timeout,
    )
    return result.stdout.strip()


def _repo_status() -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    started = time.time()

    if not RESEARCH_REPO_PATH.exists():
        return {
            "ok": False,
            "service": "veloce_repo_status",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": trace_id,
            "path": str(RESEARCH_REPO_PATH),
            "detail": "research repository path is not mounted",
        }

    try:
        branch = _run_git(RESEARCH_REPO_PATH, ["rev-parse", "--abbrev-ref", "HEAD"])
        commit = _run_git(RESEARCH_REPO_PATH, ["rev-parse", "HEAD"])
        short_commit = _run_git(RESEARCH_REPO_PATH, ["rev-parse", "--short", "HEAD"])
        dirty_lines = _run_git(
            RESEARCH_REPO_PATH,
            ["status", "--porcelain=v1", "--untracked-files=normal"],
        ).splitlines()
        last_commit = _run_git(
            RESEARCH_REPO_PATH,
            ["log", "-1", "--pretty=format:%h%x09%s%x09%cI"],
        )
    except FileNotFoundError:
        fallback = _read_git_commit(RESEARCH_REPO_PATH)
        fallback.update(
            {
                "service": "veloce_repo_status",
                "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "trace_id": trace_id,
                "dirty": None,
                "dirty_detail": "git binary is not installed in the proxy image",
            }
        )
        return fallback
    except subprocess.CalledProcessError as exc:
        return {
            "ok": False,
            "service": "veloce_repo_status",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": trace_id,
            "path": str(RESEARCH_REPO_PATH),
            "detail": exc.stderr.strip() or str(exc),
        }
    except Exception as exc:
        return {
            "ok": False,
            "service": "veloce_repo_status",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": trace_id,
            "path": str(RESEARCH_REPO_PATH),
            "detail": f"{type(exc).__name__}: {exc}",
        }

    return {
        "ok": True,
        "service": "veloce_repo_status",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": trace_id,
        "path": str(RESEARCH_REPO_PATH),
        "branch": branch,
        "commit": commit,
        "short_commit": short_commit,
        "dirty": bool(dirty_lines),
        "dirty_count": len(dirty_lines),
        "dirty_paths": dirty_lines[:30],
        "last_commit": last_commit,
        "latency_ms": int((time.time() - started) * 1000),
        "verification_hints": [
            "cd /root/veloce-research-os && git rev-parse --short HEAD",
            "cd /root/veloce-research-os && git status --short",
            "cd /root/veloce-research-os && git log -1 --oneline",
        ],
    }


def _stack_status() -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    checks = {
        "openwebui": _tcp_probe("openwebui", OPENWEBUI_URL),
        "hermes": _http_probe("hermes", f"{HERMES_URL}/health"),
        "paperclip": _http_probe("paperclip", PAPERCLIP_URL),
        "mcpo": _http_probe("mcpo", f"{MCPO_BASE_URL}/docs"),
        "research_repo": _read_git_commit(RESEARCH_REPO_PATH),
    }
    ok = all(check.get("ok") for check in checks.values())
    return {
        "ok": ok,
        "service": "veloce_stack_status",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": trace_id,
        "checks": checks,
        "verification_hints": [
            "docker ps --format 'table {{.Names}}\\t{{.Status}}'",
            "docker logs --tail=20 aiagency-mcpo-openwebui-proxy",
            "cd /root/veloce-research-os && git rev-parse --short HEAD",
        ],
    }


def _safe_read_text(path: Path, limit: int = 80_000) -> str:
    try:
        return path.read_text(encoding="utf-8")[:limit]
    except Exception:
        return ""


def _json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _contains_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def _ruflo_validation_status() -> dict[str, Any]:
    closeout = RESEARCH_REPO_PATH / "docs" / "v1.6-ruflo-planning-closeout.md"
    text = _safe_read_text(closeout)
    passed = "3 passed in 0.01s" in text and "PYTHONPATH=. pytest -q" in text
    return {
        "ok": passed,
        "source": str(closeout),
        "detail": (
            "VEL-124 validation recorded: 3 passed in 0.01s"
            if passed
            else "VEL-124 validation proof not found in mounted repo docs"
        ),
    }


def _ruflo_status() -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    started = time.time()
    sandbox = RUFLO_SANDBOX_PATH

    runtime_config = sandbox / ".claude-flow" / "config.yaml"
    claude_settings = sandbox / ".claude" / "settings.json"
    codex_config = sandbox / ".agents" / "config.toml"
    mcp_config = sandbox / ".mcp.json"
    agents_doc = sandbox / "AGENTS.md"
    claude_doc = sandbox / "CLAUDE.md"

    runtime_text = _safe_read_text(runtime_config)
    codex_text = _safe_read_text(codex_config)
    settings = _json_file(claude_settings)
    mcp = _json_file(mcp_config)

    permissions = settings.get("permissions", {}) if isinstance(settings, dict) else {}
    env = settings.get("env", {}) if isinstance(settings, dict) else {}
    claude_flow = settings.get("claudeFlow", {}) if isinstance(settings, dict) else {}
    mcp_server = (
        mcp.get("mcpServers", {}).get("ruflo", {})
        if isinstance(mcp.get("mcpServers", {}), dict)
        else {}
    )
    mcp_env = mcp_server.get("env", {}) if isinstance(mcp_server, dict) else {}

    checks = {
        "sandbox_path": {
            "ok": sandbox.exists() and sandbox.is_dir(),
            "path": str(sandbox),
            "detail": "sandbox directory exists" if sandbox.exists() else "sandbox directory missing",
        },
        "runtime_config": {
            "ok": runtime_config.exists(),
            "path": str(runtime_config),
            "detail": ".claude-flow runtime config present",
        },
        "claude_settings": {
            "ok": claude_settings.exists(),
            "path": str(claude_settings),
            "detail": "Claude/Ruflo settings present",
        },
        "codex_config": {
            "ok": codex_config.exists(),
            "path": str(codex_config),
            "detail": "Codex agent config present",
        },
        "mcp_config": {
            "ok": mcp_config.exists(),
            "path": str(mcp_config),
            "detail": "MCP config present but autoStart must remain false",
        },
        "agent_docs": {
            "ok": agents_doc.exists() and claude_doc.exists(),
            "paths": [str(agents_doc), str(claude_doc)],
            "detail": "AGENTS.md and CLAUDE.md present",
        },
        "runtime_hardened": {
            "ok": _contains_all(
                runtime_text,
                [
                    "maxAgents: 1",
                    "autoScale: false",
                    "autoExecute: false",
                    "autoStart: false",
                ],
            ),
            "detail": "runtime config disables autoscale, autoexecute, autostart and limits maxAgents to 1",
        },
        "claude_hardened": {
            "ok": (
                permissions.get("allow") == []
                and "Bash(*)" in permissions.get("deny", [])
                and "Write(*)" in permissions.get("deny", [])
                and "Edit(*)" in permissions.get("deny", [])
                and env.get("CLAUDE_FLOW_V3_ENABLED") == "false"
                and env.get("CLAUDE_FLOW_HOOKS_ENABLED") == "false"
                and claude_flow.get("enabled") is False
                and claude_flow.get("daemon", {}).get("autoStart") is False
            ),
            "detail": "Claude settings block shell/write/edit and disable Claude Flow runtime hooks",
        },
        "mcp_hardened": {
            "ok": (
                mcp_server.get("autoStart") is False
                and mcp_env.get("CLAUDE_FLOW_HOOKS_ENABLED") == "false"
                and mcp_env.get("CLAUDE_FLOW_MAX_AGENTS") == "1"
            ),
            "detail": "Ruflo MCP config is present but does not autostart",
        },
        "codex_hardened": {
            "ok": (
                'approval_policy = "on-request"' in codex_text
                and 'sandbox_mode = "workspace-write"' in codex_text
                and '"*_KEY"' in codex_text
                and '"*_SECRET"' in codex_text
            ),
            "detail": "Codex config keeps approvals and excludes secret-like environment variables",
        },
        "vel_124_validation": _ruflo_validation_status(),
    }
    ok = all(check.get("ok") for check in checks.values())

    return {
        "ok": ok,
        "service": "veloce_ruflo_status",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": trace_id,
        "sandbox_path": str(sandbox),
        "mode": "read_only_status",
        "production_enabled": False,
        "disallowed_services": [
            "daemon",
            "swarm",
            "memory",
            "hooks",
            "autopilot",
            "claude_mcp_autostart",
            "codex_mcp_autostart",
        ],
        "checks": checks,
        "latency_ms": int((time.time() - started) * 1000),
        "verification_hints": [
            "ls -la /opt/veloce-ruflo-sandbox",
            "grep -RniE 'autoExecute|autoScale|HOOKS_ENABLED|autoStart|maxAgents|enabled|Bash' /opt/veloce-ruflo-sandbox/.claude-flow/config.yaml /opt/veloce-ruflo-sandbox/.claude/settings.json /opt/veloce-ruflo-sandbox/.mcp.json",
            "docker logs --tail=20 aiagency-mcpo-openwebui-proxy",
        ],
        "next_safe_step": "Keep Ruflo planning-only. Do not start daemon, swarm, memory, hooks, or autopilot.",
    }


def _as_string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _as_labels(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_as_string(item) for item in value if _as_string(item)]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _risk_level(title: str, description: str, labels: list[str]) -> str:
    text = " ".join([title, description, " ".join(labels)]).lower()
    high_terms = [
        "production",
        "secret",
        "api key",
        "token",
        "deploy",
        "docker",
        "paperclip mutation",
        "github write",
        "autopilot",
        "daemon",
        "swarm",
    ]
    medium_terms = ["integration", "openwebui", "mcpo", "hermes", "ruflo", "paperclip"]
    if any(term in text for term in high_terms):
        return "high"
    if any(term in text for term in medium_terms):
        return "medium"
    return "low"


def _blocked_execution_request(payload: dict[str, Any]) -> str | None:
    mode = _as_string(payload.get("requested_mode"), "plan").lower()
    if mode in {
        "run",
        "exec",
        "execute",
        "apply",
        "deploy",
        "mutate",
        "write",
        "autopilot",
        "start",
    }:
        return f"requested_mode={mode} is not allowed for the planning bridge"

    for key in ("allow_execution", "execute_now", "start_services", "write_changes"):
        if payload.get(key) is True:
            return f"{key}=true is not allowed for the planning bridge"

    return None


def _paperclip_comment(plan: dict[str, Any]) -> str:
    issue_id = plan["input"]["issue_id"] or "unassigned"
    return "\n".join(
        [
            f"Ruflo planning-only bridge result for {issue_id}.",
            "",
            f"Decision: {plan['decision']}",
            f"Owner: {plan['owner']}",
            f"Risk: {plan['risk_level']}",
            "",
            "Next action:",
            plan["next_action"],
            "",
            "Verification command:",
            "```bash",
            plan["verification_command"],
            "```",
            "",
            "Rollback note:",
            plan["rollback_note"],
            "",
            "Approval gates:",
            *[f"- {gate}" for gate in plan["approval_gates"]],
            "",
            "Guardrail:",
            "Ruflo was not executed. Daemon, swarm, memory, hooks, autopilot, Claude MCP, and Codex MCP remain disabled.",
        ]
    )


def _ruflo_plan(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    started = time.time()
    blocked_reason = _blocked_execution_request(payload)
    if blocked_reason:
        return {
            "ok": False,
            "service": "veloce_ruflo_plan",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": trace_id,
            "decision": "blocked_execution_request",
            "error": blocked_reason,
            "ruflo_runtime_invoked": False,
            "production_enabled": False,
        }

    title = _as_string(payload.get("title"))
    description = _as_string(payload.get("description"))
    if not title or not description:
        return {
            "ok": False,
            "service": "veloce_ruflo_plan",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": trace_id,
            "decision": "invalid_input",
            "error": "title and description are required",
            "ruflo_runtime_invoked": False,
            "production_enabled": False,
        }

    sandbox_status = _ruflo_status()
    if not sandbox_status.get("ok"):
        return {
            "ok": False,
            "service": "veloce_ruflo_plan",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": trace_id,
            "decision": "blocked_sandbox_not_ready",
            "error": "Ruflo sandbox status is not healthy; refusing to plan",
            "sandbox_status": sandbox_status,
            "ruflo_runtime_invoked": False,
            "production_enabled": False,
        }

    issue_id = _as_string(payload.get("issue_id"))
    priority = _as_string(payload.get("priority"), "medium").lower()
    assignee = _as_string(payload.get("assignee"), "Technical Builder")
    labels = _as_labels(payload.get("labels"))
    risk_level = _risk_level(title, description, labels)
    owner = assignee or ("CEO" if risk_level == "high" else "Technical Builder")

    verification_command = (
        "curl -sS https://tools.srv1314350.hstgr.cloud/ruflo_status "
        '-H "Authorization: Bearer $MCPO_API_KEY" '
        '-H "Content-Type: application/json" '
        "-d '{\"scope\":\"sandbox\"}' | python3 -m json.tool"
    )
    next_action = (
        "Create a human-reviewed implementation issue from this plan, keep Ruflo in "
        "planning-only mode, and execute changes through GitHub/Codex with targeted tests."
    )
    if risk_level == "low":
        next_action = (
            "Use this plan as the implementation checklist, then run the listed "
            "verification command before marking the issue done."
        )
    elif risk_level == "high":
        next_action = (
            "Route this plan to human review before implementation because it touches "
            "production-sensitive surfaces or orchestration controls."
        )

    plan = {
        "ok": True,
        "service": "veloce_ruflo_plan",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": trace_id,
        "planner_engine": "veloce_guarded_planner_v0.1",
        "ruflo_runtime_invoked": False,
        "production_enabled": False,
        "input": {
            "issue_id": issue_id,
            "title": title,
            "priority": priority,
            "assignee": assignee,
            "labels": labels,
        },
        "decision": "plan_only_ready",
        "owner": owner,
        "risk_level": risk_level,
        "next_action": next_action,
        "verification_command": verification_command,
        "rollback_note": (
            "No production mutation was performed by this bridge. Rollback is to discard "
            "the generated plan/comment and leave Ruflo services stopped."
        ),
        "deliverables": [
            "human-reviewed implementation issue",
            "targeted code or configuration change",
            "verification command output",
            "Paperclip disposition comment",
        ],
        "approval_gates": [
            "human approval before any production write",
            "no secrets mounted into Ruflo",
            "no daemon/swarm/memory/hooks/autopilot start",
            "GitHub commit required for durable code changes",
            "VPS verification required before done",
        ],
        "sandbox_summary": {
            "sandbox_path": sandbox_status.get("sandbox_path"),
            "mode": sandbox_status.get("mode"),
            "production_enabled": sandbox_status.get("production_enabled"),
            "all_checks_ok": sandbox_status.get("ok"),
        },
        "latency_ms": int((time.time() - started) * 1000),
    }
    plan["paperclip_comment_markdown"] = _paperclip_comment(plan)
    return plan


class Handler(BaseHTTPRequestHandler):
    server_version = "VeloceMCPOProxy/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stdout.write("%s - %s\n" % (self.address_string(), fmt % args))
        sys.stdout.flush()

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.send_header("access-control-allow-origin", ALLOWED_ORIGIN)
        self.send_header("access-control-allow-methods", "GET, POST, OPTIONS")
        self.send_header("access-control-allow-headers", "authorization, content-type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("access-control-allow-origin", ALLOWED_ORIGIN)
        self.send_header("access-control-allow-methods", "GET, POST, OPTIONS")
        self.send_header("access-control-allow-headers", "authorization, content-type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/healthz", "/api/config"}:
            self._write_json(
                200,
                {
                    "ok": True,
                    "service": "mcpo-openwebui-proxy",
                    "upstream": MCPO_BASE_URL,
                },
            )
            return
        if self.path in {"/openapi.json", "/openapi.json/openapi.json"}:
            self._write_json(200, _openapi_spec())
            return
        self._write_json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {
            "/stack_status",
            "/repo_status",
            "/ruflo_status",
            "/ruflo_plan",
            "/get_current_time",
            "/convert_time",
        }:
            self._write_json(404, {"ok": False, "error": "not found"})
            return

        expected = f"Bearer {MCPO_API_KEY}"
        if not MCPO_API_KEY or self.headers.get("authorization") != expected:
            self._write_json(401, {"ok": False, "error": "unauthorized"})
            return

        if self.path == "/stack_status":
            self._write_json(200, _stack_status())
            return
        if self.path == "/repo_status":
            self._write_json(200, _repo_status())
            return
        if self.path == "/ruflo_status":
            self._write_json(200, _ruflo_status())
            return
        if self.path == "/ruflo_plan":
            length = int(self.headers.get("content-length", "0"))
            body = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(body.decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("JSON payload must be an object")
            except Exception as exc:
                self._write_json(
                    400,
                    {
                        "ok": False,
                        "service": "veloce_ruflo_plan",
                        "error": f"invalid JSON payload: {exc}",
                    },
                )
                return
            self._write_json(200, _ruflo_plan(payload))
            return

        length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        started = time.time()
        trace_id = str(uuid.uuid4())
        request = urllib.request.Request(
            f"{MCPO_BASE_URL}{self.path}",
            data=body,
            headers={
                "authorization": f"Bearer {MCPO_API_KEY}",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                upstream_body = response.read()
                payload = json.loads(upstream_body.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            self._write_json(
                502,
                {
                    "ok": False,
                    "trace_id": trace_id,
                    "error": f"upstream HTTP {exc.code}",
                    "detail": detail[:500],
                },
            )
            return
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self._write_json(
                502,
                {
                    "ok": False,
                    "trace_id": trace_id,
                    "error": type(exc).__name__,
                    "detail": str(exc),
                },
            )
            return

        payload.setdefault("ok", True)
        payload.setdefault("trace_id", trace_id)
        payload.setdefault("latency_ms", int((time.time() - started) * 1000))
        self._write_json(200, payload)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"mcpo-openwebui-proxy listening on :{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
