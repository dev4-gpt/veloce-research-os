from __future__ import annotations

import json
import os
from pathlib import Path
import re
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
API_SERVER_KEY = os.environ.get("API_SERVER_KEY", "")
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
GRAPHIFY_GRAPH_PATH = Path(
    os.environ.get(
        "GRAPHIFY_GRAPH_PATH",
        str(RESEARCH_REPO_PATH / "graphify-out" / "graph.json"),
    )
)
KNOWLEDGE_MEMORY_DIR = Path(
    os.environ.get("KNOWLEDGE_MEMORY_DIR", "/workspace/veloce-memory")
)
KNOWLEDGE_MEMORY_WRITE_ENABLED = (
    os.environ.get("KNOWLEDGE_MEMORY_WRITE_ENABLED", "false").lower() == "true"
)
PRODUCTION_JOB_DIR = Path(
    os.environ.get(
        "PRODUCTION_JOB_DIR",
        str(RESEARCH_REPO_PATH / "projects/reliability-policy-matrix/artifacts/derived/v2_jobs"),
    )
)
PRODUCTION_RUNNER_STATE_DIR = Path(
    os.environ.get(
        "PRODUCTION_RUNNER_STATE_DIR",
        str(RESEARCH_REPO_PATH / "projects/reliability-policy-matrix/artifacts/derived/v2_runner_state"),
    )
)
PRODUCTION_AUDIT_LEDGER = Path(
    os.environ.get(
        "PRODUCTION_AUDIT_LEDGER",
        str(RESEARCH_REPO_PATH / "projects/reliability-policy-matrix/artifacts/derived/production_execution_audit_v2_0.jsonl"),
    )
)
PRODUCTION_RUNNER_LEDGER = Path(
    os.environ.get(
        "PRODUCTION_RUNNER_LEDGER",
        str(RESEARCH_REPO_PATH / "projects/reliability-policy-matrix/artifacts/derived/production_job_runner_events_v2_1.jsonl"),
    )
)
PRODUCTION_MEMORY_EVENT_DIR = Path(
    os.environ.get(
        "PRODUCTION_MEMORY_EVENT_DIR",
        str(RESEARCH_REPO_PATH / "projects/reliability-policy-matrix/artifacts/derived/graph-memory-events"),
    )
)
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|bearer\s+[a-z0-9._~+/=-]{16,}|sk-[a-z0-9]{12,}|nvapi-[a-z0-9_-]{12,})"
)
PRODUCTION_ALLOWED_CAPABILITIES = {
    "paperclip_writeback",
    "chat_to_pr",
    "chat_to_canary_deploy",
    "autonomous_rollback",
    "long_running_agent_jobs",
    "active_alerting",
    "graph_memory_ingestion",
}
PRODUCTION_STATES = {
    "queued_dry_run",
    "approved_for_live_candidate",
    "lease_acquired",
    "running",
    "heartbeat",
    "completed",
    "blocked",
    "cancelled",
    "rollback_required",
    "rollback_prepared",
}
PRODUCTION_FORBIDDEN_PAYLOAD_KEYS = {
    "command",
    "shell",
    "docker",
    "token",
    "api_key",
    "secret",
    "password",
    "path",
    "filesystem",
    "raw",
}


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
            "/ruflo_execution_packet": {
                "post": {
                    "operationId": "ruflo_execution_packet",
                    "summary": "Create a human-approved execution packet from a Ruflo plan without running Ruflo.",
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
                                        "plan_trace_id": {"type": "string"},
                                        "approved_by": {"type": "string"},
                                        "approval": {
                                            "type": "string",
                                            "default": "human_approved",
                                        },
                                        "execution_owner": {
                                            "type": "string",
                                            "default": "Codex/GitHub",
                                        },
                                        "labels": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "requested_mode": {
                                            "type": "string",
                                            "default": "execution_packet",
                                        },
                                    },
                                    "required": ["title", "description", "approved_by"],
                                    "additionalProperties": True,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Approval-gated execution packet result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/ruflo_orchestration_dry_run": {
                "post": {
                    "operationId": "ruflo_orchestration_dry_run",
                    "summary": "Create a policy-governed Ruflo task graph without running Ruflo.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "goal": {"type": "string"},
                                        "issue_id": {"type": "string"},
                                        "requested_mode": {
                                            "type": "string",
                                            "default": "dry_run",
                                        },
                                    },
                                    "required": ["goal"],
                                    "additionalProperties": True,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Ruflo orchestration dry-run result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/hermes_memory_query": {
                "post": {
                    "operationId": "hermes_memory_query",
                    "summary": "Ask Hermes for project memory or operator context through a structured bridge.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string"},
                                        "dry_run": {"type": "boolean", "default": False},
                                    },
                                    "required": ["query"],
                                    "additionalProperties": True,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Hermes memory query result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/hermes_agent_task": {
                "post": {
                    "operationId": "hermes_agent_task",
                    "summary": "Ask Hermes to perform a structured agent reasoning task.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "task": {"type": "string"},
                                        "context": {"type": "string"},
                                        "dry_run": {"type": "boolean", "default": False},
                                    },
                                    "required": ["task"],
                                    "additionalProperties": True,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Hermes agent task result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/knowledge_graph_status": {
                "post": {
                    "operationId": "knowledge_graph_status",
                    "summary": "Inspect the local Graphify knowledge graph status.",
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
                            "description": "Graph status result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/knowledge_graph_query": {
                "post": {
                    "operationId": "knowledge_graph_query",
                    "summary": "Query the Graphify knowledge graph for repo/docs/runbook context.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "question": {"type": "string"},
                                        "max_results": {"type": "integer", "default": 8},
                                        "source_filter": {
                                            "type": "string",
                                            "enum": ["docs", "knowledge", "code", "tests", "all"],
                                            "default": "docs",
                                        },
                                        "include_relationships": {"type": "boolean", "default": True},
                                        "answer_style": {
                                            "type": "string",
                                            "enum": ["raw", "summary"],
                                            "default": "summary",
                                        },
                                    },
                                    "required": ["question"],
                                    "additionalProperties": True,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Knowledge graph query result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/knowledge_memory_record": {
                "post": {
                    "operationId": "knowledge_memory_record",
                    "summary": "Create a secret-free memory event packet for Obsidian and Graphify ingestion.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "source_system": {"type": "string"},
                                        "event_type": {"type": "string"},
                                        "summary": {"type": "string"},
                                        "evidence_refs": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "tags": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "dry_run": {"type": "boolean", "default": True},
                                    },
                                    "required": ["source_system", "event_type", "summary"],
                                    "additionalProperties": True,
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Knowledge memory record result",
                            "content": {"application/json": {"schema": {"type": "object"}}},
                        },
                        "401": {"description": "Unauthorized"},
                    },
                }
            },
            "/production_execution_status": {
                "post": {
                    "operationId": "production_execution_status",
                    "summary": "Inspect the V2 production execution runner and queued jobs.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": False,
                        "content": {"application/json": {"schema": {"type": "object", "properties": {}, "additionalProperties": False}}},
                    },
                    "responses": {"200": {"description": "Production execution status", "content": {"application/json": {"schema": {"type": "object"}}}}, "401": {"description": "Unauthorized"}},
                }
            },
            "/production_job_enqueue": {
                "post": {
                    "operationId": "production_job_enqueue",
                    "summary": "Create a typed dry-run production job packet.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "job_id": {"type": "string"},
                                        "capability": {"type": "string"},
                                        "issue_id": {"type": "string"},
                                        "budget_minutes": {"type": "integer", "default": 5},
                                        "max_attempts": {"type": "integer", "default": 1},
                                        "heartbeat_seconds": {"type": "integer", "default": 60},
                                    },
                                    "required": ["job_id", "capability"],
                                    "additionalProperties": False,
                                }
                            }
                        },
                    },
                    "responses": {"200": {"description": "Production job enqueue result", "content": {"application/json": {"schema": {"type": "object"}}}}, "401": {"description": "Unauthorized"}},
                }
            },
            "/production_job_status": {
                "post": {
                    "operationId": "production_job_status",
                    "summary": "Inspect one typed production job packet and runner state.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"], "additionalProperties": False}}},
                    },
                    "responses": {"200": {"description": "Production job status result", "content": {"application/json": {"schema": {"type": "object"}}}}, "401": {"description": "Unauthorized"}},
                }
            },
            "/production_job_cancel": {
                "post": {
                    "operationId": "production_job_cancel",
                    "summary": "Cancel a queued or running production job packet.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"type": "object", "properties": {"job_id": {"type": "string"}, "reason": {"type": "string", "default": "operator_cancelled"}}, "required": ["job_id"], "additionalProperties": False}}},
                    },
                    "responses": {"200": {"description": "Production job cancellation result", "content": {"application/json": {"schema": {"type": "object"}}}}, "401": {"description": "Unauthorized"}},
                }
            },
            "/production_job_approve": {
                "post": {
                    "operationId": "production_job_approve",
                    "summary": "Approve a queued dry-run packet as a live candidate without executing it.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"type": "object", "properties": {"job_id": {"type": "string"}, "approved_by": {"type": "string"}, "approval": {"type": "string", "default": "human_approved"}}, "required": ["job_id", "approved_by"], "additionalProperties": False}}},
                    },
                    "responses": {"200": {"description": "Production job approval result", "content": {"application/json": {"schema": {"type": "object"}}}}, "401": {"description": "Unauthorized"}},
                }
            },
            "/production_audit_tail": {
                "post": {
                    "operationId": "production_audit_tail",
                    "summary": "Return a redacted tail of V2 production execution audit events.",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": False,
                        "content": {"application/json": {"schema": {"type": "object", "properties": {"limit": {"type": "integer", "default": 20}}, "additionalProperties": False}}},
                    },
                    "responses": {"200": {"description": "Production audit tail", "content": {"application/json": {"schema": {"type": "object"}}}}, "401": {"description": "Unauthorized"}},
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


def _paperclip_execution_comment(packet: dict[str, Any]) -> str:
    issue_id = packet["input"]["issue_id"] or "unassigned"
    return "\n".join(
        [
            f"Ruflo approval-gated execution packet for {issue_id}.",
            "",
            f"Decision: {packet['decision']}",
            f"Execution owner: {packet['execution_owner']}",
            f"Approved by: {packet['approved_by']}",
            "",
            "Execution authority:",
            packet["execution_authority"],
            "",
            "Next action:",
            packet["next_action"],
            "",
            "Execution checklist:",
            *[
                f"- {step['name']}: {step['action']}"
                for step in packet["execution_packet"]["steps"]
            ],
            "",
            "Verification commands:",
            "```bash",
            *packet["execution_packet"]["verification_commands"],
            "```",
            "",
            "Rollback:",
            packet["execution_packet"]["rollback_note"],
            "",
            "Guardrail:",
            "Ruflo still did not run production work. Paperclip records this packet; Codex/GitHub/VPS perform the approved implementation and verification.",
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


def _ruflo_execution_packet(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    started = time.time()
    mode = _as_string(payload.get("requested_mode"), "execution_packet").lower()
    allowed_modes = {"execution_packet", "packet", "handoff", "approval_gated_execution"}
    if mode not in allowed_modes:
        return {
            "ok": False,
            "service": "veloce_ruflo_execution_packet",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": trace_id,
            "decision": "blocked_runtime_execution_request",
            "error": (
                "This bridge only creates an approval-gated execution packet. "
                "Use requested_mode=execution_packet; do not request runtime execution."
            ),
            "ruflo_runtime_invoked": False,
            "production_enabled": False,
        }

    for key in ("allow_runtime_execution", "execute_now", "start_services", "write_changes"):
        if payload.get(key) is True:
            return {
                "ok": False,
                "service": "veloce_ruflo_execution_packet",
                "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "trace_id": trace_id,
                "decision": "blocked_runtime_execution_request",
                "error": f"{key}=true is not allowed; create a packet only",
                "ruflo_runtime_invoked": False,
                "production_enabled": False,
            }

    title = _as_string(payload.get("title"))
    description = _as_string(payload.get("description"))
    approved_by = _as_string(payload.get("approved_by"))
    approval = _as_string(payload.get("approval")).lower()
    if not title or not description:
        return {
            "ok": False,
            "service": "veloce_ruflo_execution_packet",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": trace_id,
            "decision": "invalid_input",
            "error": "title and description are required",
            "ruflo_runtime_invoked": False,
            "production_enabled": False,
        }
    if not approved_by or approval not in {"human_approved", "approved"}:
        return {
            "ok": False,
            "service": "veloce_ruflo_execution_packet",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": trace_id,
            "decision": "blocked_missing_human_approval",
            "error": "approved_by and approval=human_approved are required",
            "ruflo_runtime_invoked": False,
            "production_enabled": False,
        }

    sandbox_status = _ruflo_status()
    if not sandbox_status.get("ok"):
        return {
            "ok": False,
            "service": "veloce_ruflo_execution_packet",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": trace_id,
            "decision": "blocked_sandbox_not_ready",
            "error": "Ruflo sandbox status is not healthy; refusing to create packet",
            "sandbox_status": sandbox_status,
            "ruflo_runtime_invoked": False,
            "production_enabled": False,
        }

    issue_id = _as_string(payload.get("issue_id"))
    labels = _as_labels(payload.get("labels"))
    execution_owner = _as_string(payload.get("execution_owner"), "Codex/GitHub")
    plan_trace_id = _as_string(payload.get("plan_trace_id"))
    risk_level = _risk_level(title, description, labels)
    verification_commands = [
        "python3 -m unittest tools/mcpo-openwebui-proxy/tests/test_ruflo_status.py",
        (
            "curl -sS https://tools.srv1314350.hstgr.cloud/ruflo_status "
            '-H "Authorization: Bearer $MCPO_API_KEY" '
            '-H "Content-Type: application/json" '
            "-d '{\"scope\":\"sandbox\"}' | python3 -m json.tool"
        ),
        "docker logs --tail=50 aiagency-mcpo-openwebui-proxy | grep ruflo",
    ]

    packet = {
        "ok": True,
        "service": "veloce_ruflo_execution_packet",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": trace_id,
        "planner_engine": "veloce_guarded_executor_packet_v0.1",
        "ruflo_runtime_invoked": False,
        "production_enabled": False,
        "decision": "approval_gated_execution_packet_ready",
        "execution_authority": (
            "manual_or_codex_only: Paperclip records the packet; Ruflo daemon, swarm, "
            "memory, hooks, autopilot, Claude MCP autostart, and Codex MCP autostart remain disabled."
        ),
        "approved_by": approved_by,
        "execution_owner": execution_owner,
        "risk_level": risk_level,
        "input": {
            "issue_id": issue_id,
            "title": title,
            "labels": labels,
            "plan_trace_id": plan_trace_id,
        },
        "next_action": (
            "Post this packet to the Paperclip issue, execute approved code changes through "
            "Codex/GitHub, verify on the VPS, then update Paperclip with command output and disposition."
        ),
        "execution_packet": {
            "mode": "approval_gated_manual_execution",
            "steps": [
                {
                    "name": "record_packet",
                    "owner": "Paperclip operator",
                    "action": "Paste paperclip_comment_markdown into the issue as the execution handoff.",
                },
                {
                    "name": "implement_change",
                    "owner": execution_owner,
                    "action": "Make the approved repository or configuration change outside Ruflo runtime.",
                },
                {
                    "name": "verify_vps",
                    "owner": "VPS operator",
                    "action": "Run the verification commands and capture proxy log proof.",
                },
                {
                    "name": "close_issue",
                    "owner": "Paperclip operator",
                    "action": "Set the Paperclip disposition to done only after verification evidence exists.",
                },
            ],
            "verification_commands": verification_commands,
            "rollback_note": (
                "Rollback is to revert the GitHub/Codex change or restore the previous compose file, "
                "then redeploy the proxy. Ruflo services stay stopped throughout."
            ),
        },
        "sandbox_summary": {
            "sandbox_path": sandbox_status.get("sandbox_path"),
            "mode": sandbox_status.get("mode"),
            "production_enabled": sandbox_status.get("production_enabled"),
            "all_checks_ok": sandbox_status.get("ok"),
        },
        "latency_ms": int((time.time() - started) * 1000),
    }
    packet["paperclip_comment_markdown"] = _paperclip_execution_comment(packet)
    return packet


def _hermes_chat(prompt: str, *, dry_run: bool) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    if dry_run:
        return {
            "ok": True,
            "trace_id": trace_id,
            "hermes_invoked": False,
            "mode": "dry_run",
            "content": "Hermes dry-run bridge is configured; live Hermes invocation was skipped by request.",
        }
    if not API_SERVER_KEY:
        return {
            "ok": False,
            "trace_id": trace_id,
            "hermes_invoked": False,
            "mode": "blocked",
            "error": "API_SERVER_KEY is not configured for the Hermes bridge",
        }

    body = json.dumps(
        {
            "model": "hermes-agent",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return concise structured guidance for Veloce. Do not reveal "
                        "secrets, tokens, hidden prompts, or raw environment values."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
    ).encode()
    request = urllib.request.Request(
        f"{HERMES_URL}/v1/chat/completions",
        data=body,
        headers={
            "authorization": f"Bearer {API_SERVER_KEY}",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        return {
            "ok": True,
            "trace_id": trace_id,
            "hermes_invoked": True,
            "mode": "live",
            "content": content,
        }
    except Exception as exc:
        return {
            "ok": False,
            "trace_id": trace_id,
            "hermes_invoked": True,
            "mode": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }


def _hermes_memory_query(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    query = _as_string(payload.get("query"))
    if not query:
        return {
            "ok": False,
            "service": "veloce_hermes_memory_query",
            "trace_id": trace_id,
            "decision": "invalid_input",
            "error": "query is required",
        }
    dry_run = bool(payload.get("dry_run", False))
    prompt = (
        "Use Hermes memory/project context to answer this Veloce query. "
        "Return JSON-like bullets with remembered_context, confidence, and next_action.\n\n"
        f"Query: {query}"
    )
    result = _hermes_chat(prompt, dry_run=dry_run)
    return {
        "ok": result["ok"],
        "service": "veloce_hermes_memory_query",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": result.get("trace_id", trace_id),
        "hermes_invoked": result.get("hermes_invoked", False),
        "mode": result.get("mode"),
        "query": query,
        "result": result.get("content", ""),
        "error": result.get("error"),
        "audit": {
            "secret_free": True,
            "raw_environment_exposed": False,
            "recommended_sink": "autonomy_audit_ledger",
        },
    }


def _hermes_agent_task(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    task = _as_string(payload.get("task"))
    context = _as_string(payload.get("context"))
    if not task:
        return {
            "ok": False,
            "service": "veloce_hermes_agent_task",
            "trace_id": trace_id,
            "decision": "invalid_input",
            "error": "task is required",
        }
    dry_run = bool(payload.get("dry_run", False))
    prompt = (
        "Perform this Veloce agent reasoning task. Return structured output with "
        "plan, risks, capability_requests, and verification. Do not request raw shell, "
        "raw Docker, secret reads, or Ruflo runtime execution.\n\n"
        f"Task: {task}\n\nContext: {context}"
    )
    result = _hermes_chat(prompt, dry_run=dry_run)
    return {
        "ok": result["ok"],
        "service": "veloce_hermes_agent_task",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": result.get("trace_id", trace_id),
        "hermes_invoked": result.get("hermes_invoked", False),
        "mode": result.get("mode"),
        "task": task,
        "context_supplied": bool(context),
        "result": result.get("content", ""),
        "error": result.get("error"),
        "capability_boundary": [
            "no raw shell",
            "no raw Docker",
            "no secret reads",
            "no Ruflo runtime execution",
        ],
    }


def _ruflo_orchestration_dry_run(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    goal = _as_string(payload.get("goal"))
    issue_id = _as_string(payload.get("issue_id"))
    mode = _as_string(payload.get("requested_mode"), "dry_run").lower()
    if mode not in {"dry_run", "orchestration_dry_run", "team_plan", "task_graph"}:
        return {
            "ok": False,
            "service": "veloce_ruflo_orchestration_dry_run",
            "trace_id": trace_id,
            "decision": "blocked_runtime_execution_request",
            "error": "only dry-run orchestration modes are allowed",
            "ruflo_runtime_invoked": False,
            "production_enabled": False,
        }
    if not goal:
        return {
            "ok": False,
            "service": "veloce_ruflo_orchestration_dry_run",
            "trace_id": trace_id,
            "decision": "invalid_input",
            "error": "goal is required",
            "ruflo_runtime_invoked": False,
            "production_enabled": False,
        }

    forbidden_terms = {
        "raw_shell": ["shell", "bash", "ssh"],
        "raw_docker_control": ["docker rm", "docker exec", "docker compose up"],
        "secret_read": ["secret", "api key", "token", ".env"],
        "ruflo_runtime_execution": ["daemon", "swarm", "autopilot", "hooks"],
        "production_write": ["deploy", "write production", "mutate production"],
    }
    lower_goal = goal.lower()
    denied = [
        {"capability": capability, "reason": "requested or implied by goal text"}
        for capability, terms in forbidden_terms.items()
        if any(term in lower_goal for term in terms)
    ]
    task_graph = [
        {
            "id": "research_context",
            "agent": "researcher",
            "capability_request": "read_repo_status",
            "policy_decision": "allow",
        },
        {
            "id": "inspect_stack",
            "agent": "operator",
            "capability_request": "read_stack_status",
            "policy_decision": "allow",
        },
        {
            "id": "plan_work",
            "agent": "ruflo_planner",
            "capability_request": "create_execution_packet",
            "policy_decision": "allow_scoped",
        },
        {
            "id": "verify",
            "agent": "tester",
            "capability_request": "run_verification_suite",
            "policy_decision": "allow",
        },
    ]
    worker_packets = [
        {
            "task_id": task["id"],
            "owner": task["agent"],
            "allowed_capability": task["capability_request"],
            "status": "packet_ready",
        }
        for task in task_graph
    ]
    return {
        "ok": True,
        "service": "veloce_ruflo_orchestration_dry_run",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": trace_id,
        "issue_id": issue_id,
        "goal": goal,
        "decision": "orchestration_dry_run_ready",
        "ruflo_runtime_invoked": False,
        "production_enabled": False,
        "task_graph": task_graph,
        "worker_packets": worker_packets,
        "denied_capabilities": denied,
        "capability_broker_summary": {
            "allowed_count": len(task_graph),
            "denied_count": len(denied),
            "raw_production_access": False,
        },
        "next_action": "Review worker packets, then execute only allowed capabilities through the Veloce capability broker.",
    }


def _load_graphify_graph() -> tuple[dict[str, Any] | None, str | None]:
    try:
        return json.loads(GRAPHIFY_GRAPH_PATH.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _graph_node_text(node: dict[str, Any]) -> str:
    parts = [
        _as_string(node.get("label")),
        _as_string(node.get("id")),
        _as_string(node.get("source_file")),
        _as_string(node.get("source_location")),
        _as_string(node.get("file_type")),
    ]
    return " ".join(part for part in parts if part)


def _graph_terms(question: str) -> list[str]:
    stop = {
        "the",
        "and",
        "for",
        "with",
        "what",
        "which",
        "that",
        "this",
        "does",
        "from",
        "into",
        "about",
        "veloce",
    }
    terms = re.findall(r"[a-z0-9_.-]+", question.lower())
    return [term for term in terms if len(term) > 2 and term not in stop]


PRODUCT_GRAPH_TERMS = {
    "openwebui",
    "hermes",
    "ruflo",
    "paperclip",
    "mcpo",
    "obsidian",
    "graphify",
    "graph.json",
    "operating graph",
    "graph-memory",
}


def _graph_source_kind(node: dict[str, Any]) -> str:
    source = _as_string(node.get("source_file")).lower()
    if not source:
        return "other"
    if source.startswith("knowledge/graph-memory/"):
        return "knowledge"
    if source.startswith("docs/") or source in {"readme.md", "system_status.md"}:
        return "docs"
    if "/tests/" in source or source.startswith("tests/") or source.endswith("_test.py") or "test_" in source:
        return "tests"
    if source.endswith((".json", ".yaml", ".yml", ".toml")):
        return "config"
    if source.endswith((".py", ".js", ".ts", ".tsx", ".mjs", ".sh", ".mdx")):
        return "code"
    return "other"


def _graph_question_intent(question: str) -> str:
    q = question.lower()
    if re.search(r"\b(test|tests|proof|validate|validation|unit|fixture|assert)\b", q):
        return "proof"
    if re.search(r"\b(memory|knowledge|obsidian|graphify|graph|context)\b", q):
        return "memory"
    if re.search(r"\b(architecture|product|connect|connection|flow|system|openwebui|hermes|ruflo|paperclip|mcpo)\b", q):
        return "architecture"
    if re.search(r"\b(code|function|method|class|endpoint|implementation)\b", q):
        return "code"
    return "general"


def _normalize_graph_source_filter(value: Any, intent: str) -> str:
    source_filter = _as_string(value).lower()
    if source_filter in {"docs", "knowledge", "code", "tests", "all"}:
        return source_filter
    if intent in {"proof", "code"} and source_filter == "":
        return "all"
    return "docs"


def _graph_source_allowed(kind: str, source_filter: str) -> bool:
    if source_filter == "all":
        return True
    if source_filter == "docs":
        return kind in {"docs", "knowledge"}
    return kind == source_filter


def _score_graph_node(
    node: dict[str, Any],
    terms: list[str],
    question: str,
    source_filter: str,
    intent: str,
) -> int:
    kind = _graph_source_kind(node)
    if not _graph_source_allowed(kind, source_filter):
        return 0

    label = _as_string(node.get("label")).lower()
    source = _as_string(node.get("source_file")).lower()
    text = _graph_node_text(node).lower()
    question_lower = question.lower()
    is_graph_memory = source.startswith("knowledge/graph-memory/")
    is_graph_memory_markdown = is_graph_memory and source.endswith(".md")
    is_graph_memory_manifest = source == "knowledge/graph-memory/manifest.json"
    if source_filter == "docs" and is_graph_memory_manifest:
        return 0
    score = 0

    for term in terms:
        if term in label:
            score += 9
        elif term in text:
            score += 3

    for term in PRODUCT_GRAPH_TERMS:
        if term in question_lower and term in text:
            score += 7

    if question_lower and question_lower in text:
        score += 18
    if score == 0:
        return 0
    if kind == "docs":
        score += 14 if intent in {"architecture", "memory", "general"} else 5
    if kind == "knowledge":
        score += 28 if intent in {"architecture", "memory", "general"} else 12
    if is_graph_memory:
        score += 16
    if is_graph_memory_markdown:
        score += 34
    if is_graph_memory_manifest:
        score -= 30
    if source == "knowledge/graph-memory/veloce-operating-graph.md":
        score += 55
    if source in {"readme.md", "system_status.md"}:
        score += 8
    if "v1.9" in source or "v1.9" in label:
        score += 5
    if "v1.9l" in source or "v1.9l" in label:
        score += 18
    if "operating graph" in question_lower and (
        "operating graph" in text or is_graph_memory_markdown
    ):
        score += 80
    if kind == "tests":
        score += 12 if source_filter == "tests" or intent == "proof" else -12
    if kind == "code" and intent in {"architecture", "memory", "general"}:
        score -= 4
    return max(score, 0)


def _summarize_graph_answer(
    question: str,
    matches: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    evidence_docs: list[str],
) -> str:
    if not matches:
        return "No graph nodes matched this question under the selected source filter."

    top_labels = [_as_string(node.get("label")) for node in matches[:3] if _as_string(node.get("label"))]
    top_docs = evidence_docs[:3]
    parts = [
        f"Graph query matched {len(matches)} node(s) for: {question}",
        f"Top evidence nodes: {', '.join(top_labels)}." if top_labels else "",
        f"Evidence docs: {', '.join(top_docs)}." if top_docs else "",
        (
            "Product-level path: OpenWebUI uses MCPO tools to query Graphify graph.json; "
            "Obsidian is the human-readable memory layer; Hermes and Ruflo can consume the returned graph context."
        ),
        f"Nearby graph relationships returned: {len(relationships)}.",
    ]
    return " ".join(part for part in parts if part)


def _knowledge_graph_status() -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    graph, error = _load_graphify_graph()
    if graph is None:
        return {
            "ok": False,
            "service": "veloce_knowledge_graph_status",
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id": trace_id,
            "graph_path": str(GRAPHIFY_GRAPH_PATH),
            "error": error,
        }

    nodes = graph.get("nodes", [])
    links = graph.get("links", [])
    communities = {
        node.get("community")
        for node in nodes
        if isinstance(node, dict) and node.get("community") is not None
    }
    source_files = {
        node.get("source_file")
        for node in nodes
        if isinstance(node, dict) and node.get("source_file")
    }
    return {
        "ok": True,
        "service": "veloce_knowledge_graph_status",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": trace_id,
        "graph_path": str(GRAPHIFY_GRAPH_PATH),
        "graph_present": True,
        "nodes": len(nodes),
        "edges": len(links),
        "communities": len(communities),
        "source_files": len(source_files),
        "built_at_commit": graph.get("built_at_commit", ""),
        "graphify_report": str(GRAPHIFY_GRAPH_PATH.with_name("GRAPH_REPORT.md")),
        "human_layer": "Obsidian",
        "machine_layer": "Graphify graph.json",
    }


def _knowledge_graph_query(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    question = _as_string(payload.get("question"))
    if not question:
        return {
            "ok": False,
            "service": "veloce_knowledge_graph_query",
            "trace_id": trace_id,
            "decision": "invalid_input",
            "error": "question is required",
        }
    graph, error = _load_graphify_graph()
    if graph is None:
        return {
            "ok": False,
            "service": "veloce_knowledge_graph_query",
            "trace_id": trace_id,
            "question": question,
            "error": error,
        }

    try:
        max_results = int(payload.get("max_results", 8) or 8)
    except (TypeError, ValueError):
        max_results = 8
    max_results = max(1, min(max_results, 20))
    intent = _graph_question_intent(question)
    source_filter = _normalize_graph_source_filter(payload.get("source_filter"), intent)
    include_relationships = bool(payload.get("include_relationships", True))
    answer_style = _as_string(payload.get("answer_style") or "summary").lower()
    if answer_style not in {"raw", "summary"}:
        answer_style = "summary"
    terms = _graph_terms(question)
    nodes = [node for node in graph.get("nodes", []) if isinstance(node, dict)]
    links = [link for link in graph.get("links", []) if isinstance(link, dict)]

    scored: list[tuple[int, str, dict[str, Any]]] = []
    for node in nodes:
        score = _score_graph_node(node, terms, question, source_filter, intent)
        if score:
            scored.append((score, _graph_source_kind(node), node))
    source_priority = {"knowledge": 0, "docs": 1, "code": 2, "config": 3, "tests": 4, "other": 5}
    scored.sort(key=lambda item: (-item[0], source_priority.get(item[1], 9), _as_string(item[2].get("label"))))
    matches = [node for _, _, node in scored[:max_results]]
    match_ids = {node.get("id") for node in matches}
    neighbor_edges = [
        link
        for link in links
        if link.get("source") in match_ids or link.get("target") in match_ids
    ][: max_results * 3] if include_relationships else []
    node_by_id = {node.get("id"): node for node in nodes}
    neighbor_nodes = []
    seen = set(match_ids)
    for link in neighbor_edges:
        for endpoint in (link.get("source"), link.get("target")):
            if endpoint not in seen and endpoint in node_by_id:
                seen.add(endpoint)
                neighbor_nodes.append(node_by_id[endpoint])

    evidence_docs = sorted(
        {
            _as_string(node.get("source_file"))
            for node in matches + neighbor_nodes
            if _as_string(node.get("source_file")).endswith((".md", ".mdx", ".txt"))
        }
    )
    formatted_matches = [
        {
            "id": node.get("id"),
            "label": node.get("label"),
            "source_file": node.get("source_file"),
            "source_location": node.get("source_location"),
            "community": node.get("community"),
        }
        for node in matches
    ]
    formatted_relationships = [
        {
            "source": link.get("source"),
            "target": link.get("target"),
            "relation": link.get("relation"),
            "source_file": link.get("source_file"),
        }
        for link in neighbor_edges
    ]
    evidence_docs = evidence_docs[:max_results]
    summary_answer = _summarize_graph_answer(
        question,
        formatted_matches,
        formatted_relationships,
        evidence_docs,
    )
    return {
        "ok": True,
        "service": "veloce_knowledge_graph_query",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "trace_id": trace_id,
        "question": question,
        "source": str(GRAPHIFY_GRAPH_PATH),
        "source_filter": source_filter,
        "ranking_mode": f"v1.9N_weighted_{source_filter}_{intent}",
        "summary_answer": summary_answer,
        "answer": (
            summary_answer
            if answer_style == "summary"
            else f"Found {len(matches)} high-signal graph node(s) and {len(neighbor_edges)} nearby relationship(s) for this question."
        ),
        "matches": formatted_matches,
        "relationships": formatted_relationships,
        "evidence_docs": evidence_docs,
        "next_action": "Use evidence_docs for human review, or pass matches into Hermes/Ruflo as structured context.",
    }


def _knowledge_memory_record(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    source_system = _as_string(payload.get("source_system"))
    event_type = _as_string(payload.get("event_type"))
    summary = _as_string(payload.get("summary"))
    evidence_refs = [_as_string(item) for item in payload.get("evidence_refs", []) if _as_string(item)]
    tags = [_as_string(item) for item in payload.get("tags", []) if _as_string(item)]
    dry_run = bool(payload.get("dry_run", True))
    if not source_system or not event_type or not summary:
        return {
            "ok": False,
            "service": "veloce_knowledge_memory_record",
            "trace_id": trace_id,
            "decision": "invalid_input",
            "error": "source_system, event_type, and summary are required",
        }
    secret_scan = "\n".join([source_system, event_type, summary, *evidence_refs, *tags])
    if SECRET_PATTERN.search(secret_scan):
        return {
            "ok": False,
            "service": "veloce_knowledge_memory_record",
            "trace_id": trace_id,
            "decision": "blocked_secret_like_content",
            "error": "memory records must not contain secret-like values",
            "record_written": False,
        }

    checked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    record_id = f"km-{checked_at.replace(':', '').replace('-', '')}-{trace_id[:8]}"
    record = {
        "id": record_id,
        "checked_at": checked_at,
        "source_system": source_system,
        "event_type": event_type,
        "summary": summary,
        "evidence_refs": evidence_refs,
        "tags": tags,
        "trace_id": trace_id,
        "secret_free": True,
    }
    markdown = "\n".join(
        [
            f"# Knowledge Memory Record {record_id}",
            "",
            f"- Time: {checked_at}",
            f"- Source system: {source_system}",
            f"- Event type: {event_type}",
            f"- Trace ID: {trace_id}",
            f"- Tags: {', '.join(tags) if tags else 'none'}",
            "",
            "## Summary",
            "",
            summary,
            "",
            "## Evidence",
            "",
            *(f"- {ref}" for ref in evidence_refs),
            "",
            "## Graph Sink",
            "",
            "Obsidian human memory -> Graphify graph.json -> OpenWebUI knowledge_graph_query.",
        ]
    )

    record_written = False
    write_error = None
    if not dry_run and KNOWLEDGE_MEMORY_WRITE_ENABLED:
        try:
            day_dir = KNOWLEDGE_MEMORY_DIR / checked_at[:10]
            day_dir.mkdir(parents=True, exist_ok=True)
            (day_dir / f"{record_id}.json").write_text(
                json.dumps(record, indent=2),
                encoding="utf-8",
            )
            (day_dir / f"{record_id}.md").write_text(markdown, encoding="utf-8")
            with (KNOWLEDGE_MEMORY_DIR / "events.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
            record_written = True
        except Exception as exc:
            write_error = f"{type(exc).__name__}: {exc}"

    return {
        "ok": write_error is None,
        "service": "veloce_knowledge_memory_record",
        "checked_at": checked_at,
        "trace_id": trace_id,
        "decision": "memory_record_ready" if write_error is None else "memory_write_failed",
        "record": record,
        "record_written": record_written,
        "dry_run": dry_run,
        "write_enabled": KNOWLEDGE_MEMORY_WRITE_ENABLED,
        "write_error": write_error,
        "obsidian_markdown": markdown,
        "next_action": "Mirror the markdown into Obsidian and rerun Graphify extraction to make this event graph-queryable.",
    }


def _production_checked_at() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _production_safe_id(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", _as_string(value)).strip("-")[:96]


def _production_digest(value: Any) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(value, sort_keys=True, default=str)))


def _production_redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _production_redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_production_redact(item) for item in value]
    return SECRET_PATTERN.sub("[redacted]", str(value))


def _production_forbidden_keys(payload: Any) -> list[str]:
    found: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key).lower()
            if key_text in PRODUCTION_FORBIDDEN_PAYLOAD_KEYS or key_text.endswith(
                ("_token", "_secret", "_password", "_api_key")
            ):
                found.add(str(key))
            found.update(_production_forbidden_keys(value))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_production_forbidden_keys(item))
    return sorted(found)


def _production_secret_like(payload: Any) -> bool:
    if isinstance(payload, dict):
        return any(_production_secret_like(value) for value in payload.values())
    if isinstance(payload, list):
        return any(_production_secret_like(value) for value in payload)
    if isinstance(payload, (bool, int, float)) or payload is None:
        return False
    return bool(SECRET_PATTERN.search(str(payload)))


def _production_job_path(job_id: str) -> Path:
    return PRODUCTION_JOB_DIR / f"{_production_safe_id(job_id)}.json"


def _production_state_path(job_id: str) -> Path:
    return PRODUCTION_RUNNER_STATE_DIR / f"{_production_safe_id(job_id)}.json"


def _production_read_json(path: Path, default: Any | None = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _production_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _production_append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def _production_base_response(
    service: str,
    trace_id: str,
    decision: str,
    job_id: str = "",
    capability: str = "",
    ok: bool = True,
    errors: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "ok": ok,
        "service": service,
        "checked_at": _production_checked_at(),
        "trace_id": trace_id,
        "decision": decision,
        "job_id": job_id,
        "capability": capability,
        "audit_refs": [str(PRODUCTION_RUNNER_LEDGER), str(PRODUCTION_AUDIT_LEDGER)],
        "errors": errors or [],
        "next_action": "Inspect production_job_status, approve a queued candidate, cancel unsafe work, or run the durable runner from the VPS.",
    }
    if extra:
        payload.update(extra)
    return payload


def _production_event(
    trace_id: str,
    job_id: str,
    capability: str,
    transition: str,
    decision: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "checked_at": _production_checked_at(),
        "trace_id": trace_id,
        "job_id": job_id,
        "capability": capability,
        "transition": transition,
        "decision": decision,
        "details": _production_redact(details or {}),
        "secret_free": True,
    }
    _production_append_jsonl(PRODUCTION_RUNNER_LEDGER, event)
    _production_append_jsonl(PRODUCTION_AUDIT_LEDGER, event)
    PRODUCTION_MEMORY_EVENT_DIR.mkdir(parents=True, exist_ok=True)
    memory_name = f"{event['checked_at'].replace(':', '').replace('-', '')}-{job_id}-{transition}.md"
    (PRODUCTION_MEMORY_EVENT_DIR / memory_name).write_text(
        "\n".join(
            [
                f"# Production Job Event {job_id}",
                "",
                f"- Time: {event['checked_at']}",
                f"- Trace ID: {trace_id}",
                f"- Capability: {capability}",
                f"- Transition: {transition}",
                f"- Decision: {decision}",
                "",
                "OpenWebUI -> MCPO production execution API -> durable runner -> audit ledger -> Obsidian/Graphify memory.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return event


def _production_packet_errors(packet: dict[str, Any]) -> list[str]:
    errors = []
    if not _production_safe_id(packet.get("id")):
        errors.append("job_id is required")
    capability = _as_string(packet.get("capability"))
    if capability not in PRODUCTION_ALLOWED_CAPABILITIES:
        errors.append(f"capability is not allowlisted: {capability}")
    if _as_string(packet.get("status", "queued_dry_run")) not in PRODUCTION_STATES:
        errors.append("status is not a valid production runner state")
    forbidden = _production_forbidden_keys(packet)
    if forbidden:
        errors.append(f"forbidden payload keys: {', '.join(forbidden)}")
    if _production_secret_like(packet):
        errors.append("secret-like content is not allowed")
    return errors


def _production_job_enqueue(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    if _production_forbidden_keys(payload) or _production_secret_like(payload):
        return _production_base_response(
            "production_job_enqueue",
            trace_id,
            "blocked_unsafe_payload",
            ok=False,
            errors=["endpoint does not accept raw commands, paths, tokens, or secret-like content"],
        )
    job_id = _production_safe_id(payload.get("job_id"))
    capability = _as_string(payload.get("capability"))
    try:
        budget_minutes = max(1, min(int(payload.get("budget_minutes", 5) or 5), 240))
        max_attempts = max(1, min(int(payload.get("max_attempts", 1) or 1), 5))
        heartbeat_seconds = max(10, min(int(payload.get("heartbeat_seconds", 60) or 60), 3600))
    except (TypeError, ValueError):
        return _production_base_response(
            "production_job_enqueue",
            trace_id,
            "invalid_numeric_budget",
            job_id,
            capability,
            ok=False,
            errors=["budget_minutes, max_attempts, and heartbeat_seconds must be integers"],
        )
    packet = {
        "id": job_id,
        "issue_id": _as_string(payload.get("issue_id") or "VEL-v2.1"),
        "capability": capability,
        "status": "queued_dry_run",
        "policy_decision": "dry_run_ready",
        "budget_minutes": budget_minutes,
        "max_attempts": max_attempts,
        "heartbeat_seconds": heartbeat_seconds,
        "lease_owner": "",
        "created_at": _production_checked_at(),
        "input_hash": _production_digest(payload),
        "secret_free": True,
    }
    errors = _production_packet_errors(packet)
    if errors:
        return _production_base_response(
            "production_job_enqueue",
            trace_id,
            "blocked_invalid_packet",
            job_id,
            capability,
            ok=False,
            errors=errors,
        )
    state = {
        "job_id": job_id,
        "capability": capability,
        "state": "queued_dry_run",
        "attempts": 0,
        "lease_owner": "",
        "lease_expires_at": 0,
        "last_transition_at": _production_checked_at(),
        "trace_id": trace_id,
        "idempotency_key": _production_digest({"job_id": job_id, "capability": capability}),
        "job_input_hash": packet["input_hash"],
        "secret_free": True,
    }
    _production_write_json(_production_job_path(job_id), packet)
    _production_write_json(_production_state_path(job_id), state)
    event = _production_event(trace_id, job_id, capability, "enqueue", "queued_dry_run", {"source": "openwebui"})
    return _production_base_response(
        "production_job_enqueue",
        trace_id,
        "queued_dry_run",
        job_id,
        capability,
        extra={"job": packet, "state": state, "event": event},
    )


def _production_job_status(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    job_id = _production_safe_id(payload.get("job_id"))
    if not job_id:
        return _production_base_response("production_job_status", trace_id, "invalid_input", ok=False, errors=["job_id is required"])
    job = _production_read_json(_production_job_path(job_id), None)
    state = _production_read_json(_production_state_path(job_id), {})
    if not isinstance(job, dict):
        return _production_base_response("production_job_status", trace_id, "not_found", job_id, ok=False, errors=["job not found"])
    return _production_base_response(
        "production_job_status",
        trace_id,
        "status_ready",
        job_id,
        _as_string(job.get("capability")),
        extra={"job": _production_redact(job), "state": _production_redact(state)},
    )


def _production_execution_status() -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    jobs = []
    for path in sorted(PRODUCTION_JOB_DIR.glob("*.json")):
        job = _production_read_json(path, {})
        if not isinstance(job, dict):
            continue
        job_id = _as_string(job.get("id") or path.stem)
        state = _production_read_json(_production_state_path(job_id), {})
        jobs.append(
            {
                "job_id": job_id,
                "capability": job.get("capability", ""),
                "job_status": job.get("status", ""),
                "runner_state": state.get("state", job.get("status", "")) if isinstance(state, dict) else job.get("status", ""),
                "last_transition_at": state.get("last_transition_at", "") if isinstance(state, dict) else "",
            }
        )
    return _production_base_response(
        "production_execution_status",
        trace_id,
        "status_ready",
        extra={
            "job_count": len(jobs),
            "jobs": jobs,
            "runner_states": sorted(PRODUCTION_STATES),
            "mode": "dry_run_default",
        },
    )


def _production_job_approve(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    job_id = _production_safe_id(payload.get("job_id"))
    approved_by = _as_string(payload.get("approved_by"))
    approval = _as_string(payload.get("approval") or "human_approved")
    if _production_secret_like(payload):
        return _production_base_response("production_job_approve", trace_id, "blocked_secret_like_content", job_id, ok=False, errors=["approval payload contains secret-like content"])
    job = _production_read_json(_production_job_path(job_id), None)
    if not isinstance(job, dict):
        return _production_base_response("production_job_approve", trace_id, "not_found", job_id, ok=False, errors=["job not found"])
    capability = _as_string(job.get("capability"))
    if approval != "human_approved" or not approved_by:
        return _production_base_response("production_job_approve", trace_id, "blocked_missing_human_approval", job_id, capability, ok=False, errors=["human_approved approval and approved_by are required"])
    state = _production_read_json(_production_state_path(job_id), {})
    if not isinstance(state, dict):
        state = {}
    if state.get("state") in {"completed", "cancelled"}:
        return _production_base_response("production_job_approve", trace_id, "blocked_terminal_state", job_id, capability, ok=False, errors=[f"job is already {state.get('state')}"])
    job["status"] = "approved_for_live_candidate"
    state.update(
        {
            "job_id": job_id,
            "capability": capability,
            "state": "approved_for_live_candidate",
            "approved_by": approved_by,
            "approved_at": _production_checked_at(),
            "last_transition_at": _production_checked_at(),
            "trace_id": state.get("trace_id") or trace_id,
            "idempotency_key": state.get("idempotency_key") or _production_digest({"job_id": job_id, "capability": capability}),
            "job_input_hash": job.get("input_hash", ""),
            "secret_free": True,
        }
    )
    _production_write_json(_production_job_path(job_id), job)
    _production_write_json(_production_state_path(job_id), state)
    event = _production_event(trace_id, job_id, capability, "approve", "approved_for_live_candidate", {"approved_by": approved_by})
    return _production_base_response("production_job_approve", trace_id, "approved_for_live_candidate", job_id, capability, extra={"state": state, "event": event})


def _production_job_cancel(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    job_id = _production_safe_id(payload.get("job_id"))
    reason = _as_string(payload.get("reason") or "operator_cancelled")[:240]
    if _production_secret_like(payload):
        return _production_base_response("production_job_cancel", trace_id, "blocked_secret_like_content", job_id, ok=False, errors=["cancel payload contains secret-like content"])
    job = _production_read_json(_production_job_path(job_id), None)
    if not isinstance(job, dict):
        return _production_base_response("production_job_cancel", trace_id, "not_found", job_id, ok=False, errors=["job not found"])
    capability = _as_string(job.get("capability"))
    state = _production_read_json(_production_state_path(job_id), {})
    if not isinstance(state, dict):
        state = {}
    job["status"] = "cancelled"
    state.update(
        {
            "job_id": job_id,
            "capability": capability,
            "state": "cancelled",
            "cancel_reason": reason,
            "last_transition_at": _production_checked_at(),
            "lease_owner": "",
            "lease_expires_at": 0,
            "trace_id": state.get("trace_id") or trace_id,
            "idempotency_key": state.get("idempotency_key") or _production_digest({"job_id": job_id, "capability": capability}),
            "job_input_hash": job.get("input_hash", ""),
            "secret_free": True,
        }
    )
    _production_write_json(_production_job_path(job_id), job)
    _production_write_json(_production_state_path(job_id), state)
    event = _production_event(trace_id, job_id, capability, "cancel", "cancelled", {"reason": reason})
    return _production_base_response("production_job_cancel", trace_id, "cancelled", job_id, capability, extra={"state": state, "event": event})


def _production_audit_tail(payload: dict[str, Any]) -> dict[str, Any]:
    trace_id = str(uuid.uuid4())
    try:
        limit = max(1, min(int(payload.get("limit", 20) or 20), 100))
    except (TypeError, ValueError):
        limit = 20
    records = []
    for path in (PRODUCTION_AUDIT_LEDGER, PRODUCTION_RUNNER_LEDGER):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return _production_base_response(
        "production_audit_tail",
        trace_id,
        "audit_tail_ready",
        extra={"records": _production_redact(records[-limit:]), "limit": limit},
    )


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
            "/ruflo_execution_packet",
            "/ruflo_orchestration_dry_run",
            "/hermes_memory_query",
            "/hermes_agent_task",
            "/knowledge_graph_status",
            "/knowledge_graph_query",
            "/knowledge_memory_record",
            "/production_execution_status",
            "/production_job_enqueue",
            "/production_job_status",
            "/production_job_cancel",
            "/production_job_approve",
            "/production_audit_tail",
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
        if self.path == "/ruflo_execution_packet":
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
                        "service": "veloce_ruflo_execution_packet",
                        "error": f"invalid JSON payload: {exc}",
                    },
                )
                return
            self._write_json(200, _ruflo_execution_packet(payload))
            return
        if self.path in {
            "/ruflo_orchestration_dry_run",
            "/hermes_memory_query",
            "/hermes_agent_task",
            "/knowledge_graph_status",
            "/knowledge_graph_query",
            "/knowledge_memory_record",
            "/production_execution_status",
            "/production_job_enqueue",
            "/production_job_status",
            "/production_job_cancel",
            "/production_job_approve",
            "/production_audit_tail",
        }:
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
                        "service": self.path.strip("/"),
                        "error": f"invalid JSON payload: {exc}",
                    },
                )
                return
            if self.path == "/ruflo_orchestration_dry_run":
                self._write_json(200, _ruflo_orchestration_dry_run(payload))
                return
            if self.path == "/hermes_memory_query":
                self._write_json(200, _hermes_memory_query(payload))
                return
            if self.path == "/hermes_agent_task":
                self._write_json(200, _hermes_agent_task(payload))
                return
            if self.path == "/knowledge_graph_status":
                self._write_json(200, _knowledge_graph_status())
                return
            if self.path == "/knowledge_graph_query":
                self._write_json(200, _knowledge_graph_query(payload))
                return
            if self.path == "/knowledge_memory_record":
                self._write_json(200, _knowledge_memory_record(payload))
                return
            if self.path == "/production_execution_status":
                self._write_json(200, _production_execution_status())
                return
            if self.path == "/production_job_enqueue":
                self._write_json(200, _production_job_enqueue(payload))
                return
            if self.path == "/production_job_status":
                self._write_json(200, _production_job_status(payload))
                return
            if self.path == "/production_job_cancel":
                self._write_json(200, _production_job_cancel(payload))
                return
            if self.path == "/production_job_approve":
                self._write_json(200, _production_job_approve(payload))
                return
            self._write_json(200, _production_audit_tail(payload))
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
