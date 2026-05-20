from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
from typing import Any


def _load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    return data


def _json_path(payload: Any, dotted_path: str) -> Any:
    current = payload
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise KeyError(dotted_path)
    return current


def _assert_expected_json(payload: Any, expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for dotted_path, expected_value in expected.items():
        try:
            actual_value = _json_path(payload, dotted_path)
        except KeyError:
            errors.append(f"missing JSON field {dotted_path}")
            continue
        if actual_value != expected_value:
            errors.append(
                f"JSON field {dotted_path} expected {expected_value!r}, got {actual_value!r}"
            )
    return errors


def _run_check(check: dict[str, Any], timeout: int) -> dict[str, Any]:
    started = time.time()
    method = str(check.get("method", "GET")).upper()
    url = str(check["url"])
    headers = {"User-Agent": "veloce-stack-health/0.1"}
    body = None

    auth_env = check.get("auth_env")
    if auth_env:
        token = os.environ.get(str(auth_env), "")
        if not token:
            return {
                "name": check.get("name"),
                "ok": False,
                "url": url,
                "method": method,
                "status": None,
                "latency_ms": int((time.time() - started) * 1000),
                "errors": [f"missing required environment variable {auth_env}"],
            }
        headers["Authorization"] = f"Bearer {token}"

    if "request_json" in check:
        body = json.dumps(check["request_json"]).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    status = None
    response_text = ""
    errors: list[str] = []

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            response_text = response.read(20000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        response_text = exc.read(20000).decode("utf-8", errors="replace")
        errors.append(f"HTTPError: {exc.code}")
    except Exception as exc:  # pragma: no cover - depends on network failure mode
        errors.append(f"{exc.__class__.__name__}: {exc}")

    expected_http = check.get("expected_http")
    if expected_http is not None and status != expected_http:
        errors.append(f"HTTP status expected {expected_http}, got {status}")

    parsed_json = None
    if check.get("expect_json"):
        try:
            parsed_json = json.loads(response_text)
        except json.JSONDecodeError as exc:
            errors.append(f"response was not valid JSON: {exc}")
        else:
            errors.extend(_assert_expected_json(parsed_json, check["expect_json"]))

    latency_ms = int((time.time() - started) * 1000)
    return {
        "name": check.get("name"),
        "ok": not errors,
        "url": url,
        "method": method,
        "status": status,
        "latency_ms": latency_ms,
        "errors": errors,
        "trace_id": parsed_json.get("trace_id") if isinstance(parsed_json, dict) else None,
    }


def run(config_path: Path, output_path: Path | None = None) -> dict[str, Any]:
    config = _load_config(config_path)
    timeout = int(config.get("timeout_seconds", 10))
    checks = config.get("checks", [])
    if not isinstance(checks, list):
        raise ValueError("checks must be a list")

    results = [_run_check(check, timeout) for check in checks]
    report = {
        "ok": all(result["ok"] for result in results),
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": str(config_path),
        "results": results,
    }

    target = output_path or Path(str(config.get("generated_report", "")))
    if target:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Veloce stack health checks.")
    parser.add_argument(
        "--config",
        default="configs/stack_health_v1_7C.json",
        help="JSON health-check config path.",
    )
    parser.add_argument("--out", default=None, help="Optional output report path.")
    args = parser.parse_args()

    report = run(Path(args.config), Path(args.out) if args.out else None)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
