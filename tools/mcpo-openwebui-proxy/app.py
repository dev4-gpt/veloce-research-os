from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


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


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2).encode("utf-8")


def _openapi_spec() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Veloce MCPO Time Proxy",
            "version": "0.1.0",
            "description": "Open WebUI-compatible proxy for the MCPO time server.",
        },
        "servers": [{"url": PUBLIC_BASE_URL}],
        "paths": {
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
        if self.path == "/healthz":
            self._write_json(
                200,
                {
                    "ok": True,
                    "service": "mcpo-openwebui-proxy",
                    "upstream": MCPO_BASE_URL,
                },
            )
            return
        if self.path == "/openapi.json":
            self._write_json(200, _openapi_spec())
            return
        self._write_json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {"/get_current_time", "/convert_time"}:
            self._write_json(404, {"ok": False, "error": "not found"})
            return

        expected = f"Bearer {MCPO_API_KEY}"
        if not MCPO_API_KEY or self.headers.get("authorization") != expected:
            self._write_json(401, {"ok": False, "error": "unauthorized"})
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
