from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any


PASS = "pass"


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    return data


def _summarize(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    gates = config.get("gates", [])
    if not isinstance(gates, list):
        raise ValueError("gates must be a list")

    failures = [gate for gate in gates if gate.get("status") != PASS]
    critical_failures = [
        gate for gate in failures if gate.get("severity") == "critical"
    ]
    warning_failures = [
        gate for gate in failures if gate.get("severity") != "critical"
    ]

    status = "ready" if not critical_failures else "blocked"
    return {
        "ok": status == "ready",
        "status": status,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": str(config_path),
        "target_state": config.get("target_state", ""),
        "current_recommendation": config.get("current_recommendation", ""),
        "gate_count": len(gates),
        "critical_failures": len(critical_failures),
        "warning_failures": len(warning_failures),
        "gates": gates,
        "next_actions": [
            {
                "id": gate.get("id", ""),
                "owner": gate.get("owner", ""),
                "action": gate.get("action", ""),
                "evidence_required": gate.get("evidence_required", ""),
            }
            for gate in critical_failures
        ],
        "forbidden_until_ready": config.get("forbidden_until_ready", []),
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# V1.8 Autonomy Readiness Gate Result",
        "",
        f"Checked at: `{report['checked_at']}`",
        f"Target state: `{report['target_state']}`",
        f"Status: `{report['status']}`",
        f"Critical failures: `{report['critical_failures']}`",
        f"Warning failures: `{report['warning_failures']}`",
        "",
        "## Gate Matrix",
        "",
        "| ID | Area | Severity | Status | Owner | Evidence Required |",
        "|---|---|---|---|---|---|",
    ]
    for gate in report["gates"]:
        lines.append(
            "| {id} | {area} | {severity} | {status} | {owner} | {evidence} |".format(
                id=gate.get("id", ""),
                area=gate.get("area", ""),
                severity=gate.get("severity", ""),
                status=gate.get("status", ""),
                owner=gate.get("owner", ""),
                evidence=str(gate.get("evidence_required", "")).replace("|", "/"),
            )
        )

    lines.extend(["", "## Next Actions", ""])
    if report["next_actions"]:
        for item in report["next_actions"]:
            lines.extend(
                [
                    f"### {item['id']}",
                    "",
                    f"Owner: `{item['owner']}`",
                    "",
                    f"Action: {item['action']}",
                    "",
                    f"Evidence required: {item['evidence_required']}",
                    "",
                ]
            )
    else:
        lines.append("No blocking next actions.")

    lines.extend(["", "## Forbidden Until Ready", ""])
    lines.extend(f"- `{item}`" for item in report["forbidden_until_ready"])
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
    parser = argparse.ArgumentParser(description="Run V1.8 autonomy readiness gate.")
    parser.add_argument(
        "--config",
        default="configs/autonomy_readiness_v1_8.json",
        help="JSON autonomy-readiness config path.",
    )
    args = parser.parse_args()

    report = run(Path(args.config))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
