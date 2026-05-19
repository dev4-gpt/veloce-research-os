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
