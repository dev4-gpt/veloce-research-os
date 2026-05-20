from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    return data


def _summarize(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    controls = config.get("controls", [])
    if not isinstance(controls, list):
        raise ValueError("controls must be a list")

    failures = [c for c in controls if c.get("status") != "pass"]
    critical_failures = [
        c for c in failures if c.get("severity") == "critical"
    ]
    warning_failures = [
        c for c in failures if c.get("severity") != "critical"
    ]

    return {
        "ok": not critical_failures,
        "status": "pass" if not critical_failures else "fail",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": str(config_path),
        "control_count": len(controls),
        "critical_failures": len(critical_failures),
        "warning_failures": len(warning_failures),
        "controls": controls,
        "safe_openwebui_endpoints": config.get("safe_openwebui_endpoints", []),
        "forbidden_openwebui_endpoints": config.get("forbidden_openwebui_endpoints", []),
        "secret_rotation": config.get("secret_rotation", []),
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# V1.7D Security Access Review Result",
        "",
        f"Checked at: `{report['checked_at']}`",
        f"Status: `{report['status']}`",
        f"Critical failures: `{report['critical_failures']}`",
        f"Warning failures: `{report['warning_failures']}`",
        "",
        "## Risk Table",
        "",
        "| ID | Area | Severity | Status | Recommendation |",
        "|---|---|---|---|---|",
    ]
    for control in report["controls"]:
        lines.append(
            "| {id} | {area} | {severity} | {status} | {recommendation} |".format(
                id=control.get("id", ""),
                area=control.get("area", ""),
                severity=control.get("severity", ""),
                status=control.get("status", ""),
                recommendation=str(control.get("recommendation", "")).replace("|", "/"),
            )
        )

    lines.extend(["", "## Safe Open WebUI Endpoints", ""])
    lines.extend(f"- `{endpoint}`" for endpoint in report["safe_openwebui_endpoints"])
    lines.extend(["", "## Forbidden Open WebUI Endpoints", ""])
    lines.extend(f"- `{endpoint}`" for endpoint in report["forbidden_openwebui_endpoints"])
    lines.extend(["", "## Secret Rotation", ""])
    for item in report["secret_rotation"]:
        lines.append(
            f"- `{item.get('secret')}`: owner `{item.get('owner')}`, rotate {item.get('when')}"
        )
    lines.append("")
    return "\n".join(lines)


def run(config_path: Path) -> dict[str, Any]:
    config = _load(config_path)
    report = _summarize(config, config_path)

    json_path = Path(str(config.get("generated_json", "")))
    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    markdown_path = Path(str(config.get("generated_markdown", "")))
    if markdown_path:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(_markdown(report), encoding="utf-8")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V1.7D security/access review.")
    parser.add_argument(
        "--config",
        default="configs/access_review_v1_7D.json",
        help="JSON access-review config path.",
    )
    args = parser.parse_args()

    report = run(Path(args.config))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
