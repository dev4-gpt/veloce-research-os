from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid


HOST = os.getenv("STATUS_TOOL_HOST", "0.0.0.0")
PORT = int(os.getenv("STATUS_TOOL_PORT", "8080"))
API_KEY = os.getenv("STATUS_TOOL_API_KEY", "")
REPO_PATH = Path(os.getenv("RESEARCH_REPO_PATH", "/repo"))

TARGET_URLS = {
    "openwebui": os.getenv("OPENWEBUI_HEALTH_URL", "http://openwebui:8080/api/version"),
    "hermes": os.getenv("HERMES_HEALTH_URL", "http://hermes:8642/health"),
    "paperclip": os.getenv("PAPERCLIP_HEALTH_URL", "http://paperclip:3100/"),
}

OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "Veloce Status Check Tool",
        "version": "0.1.0",
        "description": "A narrow OpenAPI tool server for checking Veloce AI stack status.",
    },
    "servers": [{"url": "/"}],
    "paths": {
        "/status_check": {
            "post": {
                "operationId": "status_check",
                "summary": "Check one allowlisted Veloce stack target.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "target": {
                                        "type": "string",
                                        "enum": ["openwebui", "hermes", "paperclip", "research_repo"],
                                    },
                                    "timeout_ms": {
                                        "type": "integer",
                                        "minimum": 500,
                                        "maximum": 5000,
                                        "default": 1500,
                                    },
                                },
                                "required": ["target"],
                                "additionalProperties": False,
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Status result",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "ok": {"type": "boolean"},
                                        "target": {"type": "string"},
                                        "latency_ms": {"type": "integer"},
                                        "checked_at": {"type": "string"},
                                        "detail": {"type": "string"},
                                        "trace_id": {"type": "string"},
                                    },
                                    "required": ["ok", "target", "latency_ms", "checked_at", "detail", "trace_id"],
                                }
                            }
                        },
                    },
                    "400": {"description": "Invalid request"},
                    "401": {"description": "Unauthorized"},
                },
            }
        }
    },
}

if API_KEY:
    OPENAPI_SPEC["components"] = {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
            }
        }
    }
    OPENAPI_SPEC["paths"]["/status_check"]["post"]["security"] = [{"BearerAuth": []}]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def clamp_timeout_ms(value: Any) -> int:
    try:
        timeout_ms = int(value)
    except (TypeError, ValueError):
        timeout_ms = 1500
    return max(500, min(timeout_ms, 5000))


def status_payload(ok: bool, target: str, detail: str, latency_ms: int, trace_id: str) -> dict[str, Any]:
    return {
        "ok": ok,
        "target": target,
        "latency_ms": latency_ms,
        "checked_at": utc_now(),
        "detail": detail[:500],
        "trace_id": trace_id,
    }


def check_http_target(target: str, timeout_ms: int, trace_id: str) -> dict[str, Any]:
    started = time.monotonic()
    url = TARGET_URLS[target]
    request = Request(url, headers={"User-Agent": "veloce-status-check/0.1.0"})
    try:
        with urlopen(request, timeout=timeout_ms / 1000) as response:
            body = response.read(300).decode("utf-8", errors="replace").strip()
            latency_ms = int((time.monotonic() - started) * 1000)
            detail = f"HTTP {response.status} from {target}"
            if body:
                detail = f"{detail}: {body}"
            return status_payload(200 <= response.status < 500, target, detail, latency_ms, trace_id)
    except HTTPError as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        return status_payload(False, target, f"HTTP {exc.code} from {target}", latency_ms, trace_id)
    except (TimeoutError, URLError, OSError) as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        return status_payload(False, target, f"{target} check failed: {exc.__class__.__name__}", latency_ms, trace_id)


def check_research_repo(trace_id: str) -> dict[str, Any]:
    started = time.monotonic()
    required_paths = [
        REPO_PATH / "SYSTEM_STATUS.md",
        REPO_PATH / "docs" / "v1.2-design-review.md",
        REPO_PATH / "projects" / "reliability-policy-matrix",
    ]
    missing = [str(path.relative_to(REPO_PATH)) for path in required_paths if not path.exists()]
    latency_ms = int((time.monotonic() - started) * 1000)
    if missing:
        return status_payload(False, "research_repo", f"missing: {', '.join(missing)}", latency_ms, trace_id)
    return status_payload(True, "research_repo", "research repo mounted and required paths exist", latency_ms, trace_id)


def run_status_check(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    target = payload.get("target")
    trace_id = str(uuid.uuid4())
    if target not in {"openwebui", "hermes", "paperclip", "research_repo"}:
        return 400, {
            "ok": False,
            "target": str(target),
            "latency_ms": 0,
            "checked_at": utc_now(),
            "detail": "invalid target; allowed targets are openwebui, hermes, paperclip, research_repo",
            "trace_id": trace_id,
        }

    if target == "research_repo":
        return 200, check_research_repo(trace_id)

    timeout_ms = clamp_timeout_ms(payload.get("timeout_ms", 1500))
    return 200, check_http_target(str(target), timeout_ms, trace_id)


class Handler(BaseHTTPRequestHandler):
    server_version = "VeloceStatusCheck/0.1.0"

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self) -> bool:
        if not API_KEY:
            return True
        return self.headers.get("Authorization", "") == f"Bearer {API_KEY}"

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._write_json(200, {"ok": True, "service": "status_check", "checked_at": utc_now()})
            return
        if self.path == "/openapi.json":
            if API_KEY and not self._authorized():
                self._write_json(401, {"ok": False, "detail": "unauthorized"})
                return
            self._write_json(200, OPENAPI_SPEC)
            return
        self._write_json(404, {"ok": False, "detail": "not found"})

    def do_POST(self) -> None:
        if self.path != "/status_check":
            self._write_json(404, {"ok": False, "detail": "not found"})
            return
        if not self._authorized():
            self._write_json(401, {"ok": False, "detail": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except (ValueError, json.JSONDecodeError):
            self._write_json(400, {"ok": False, "detail": "invalid json"})
            return
        status, result = run_status_check(payload)
        self._write_json(status, result)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"status_check server listening on {HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
