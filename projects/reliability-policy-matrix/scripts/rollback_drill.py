from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


SECRET_MARKERS = (
    "KEY",
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "API",
    "AUTH",
)


def _load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _redact_text(text: str) -> str:
    redacted_lines = []
    for line in text.splitlines():
        upper = line.upper()
        if any(marker in upper for marker in SECRET_MARKERS):
            redacted_lines.append("[REDACTED secret-bearing line]")
        else:
            redacted_lines.append(line)
    return "\n".join(redacted_lines)


def _latest_dir(root: Path) -> Path | None:
    if not root.exists():
        return None
    dirs = sorted(path for path in root.iterdir() if path.is_dir())
    return dirs[-1] if dirs else None


def _run(command: list[str], cwd: Path, capture_output: bool = True) -> dict[str, Any]:
    started = time.time()
    if not cwd.exists():
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": 127,
            "latency_ms": int((time.time() - started) * 1000),
            "stdout": "",
            "stderr": f"working directory does not exist: {cwd}",
        }
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = proc.stdout[-5000:] if capture_output else "[suppressed]"
    stderr = proc.stderr[-5000:] if capture_output else "[suppressed]"
    return {
        "command": command,
        "cwd": str(cwd),
        "returncode": proc.returncode,
        "latency_ms": int((time.time() - started) * 1000),
        "stdout": _redact_text(stdout),
        "stderr": _redact_text(stderr),
    }


def run(config_path: Path) -> dict[str, Any]:
    config = _load(config_path)
    repo_dir = Path(config["repo_dir"])
    compose_dir = Path(config["compose_dir"])
    backup_root = Path(config["backup_root"])
    restore_root = Path(config["restore_root"])
    rendered_compose_path = Path(config["rendered_compose_path"])

    checks: list[dict[str, Any]] = []

    commit_result = _run(["git", "rev-parse", "--short", "HEAD"], repo_dir)
    checks.append(
        {
            "name": "record_current_commit",
            "ok": commit_result["returncode"] == 0,
            "detail": commit_result,
        }
    )

    compose_hashes = []
    for rel_path in config["compose_files"]:
        path = compose_dir / rel_path
        compose_hashes.append(
            {
                "path": str(path),
                "exists": path.exists(),
                "sha256": _sha256(path) if path.exists() else None,
            }
        )
    checks.append(
        {
            "name": "compose_files_present",
            "ok": all(item["exists"] for item in compose_hashes),
            "detail": compose_hashes,
        }
    )

    latest_backup = _latest_dir(backup_root)
    backup_ok = bool(latest_backup and (latest_backup / "SHA256SUMS").exists())
    checksum_result = None
    if latest_backup:
        checksum_result = _run(["sha256sum", "-c", "SHA256SUMS"], latest_backup)
    checks.append(
        {
            "name": "latest_backup_checksum",
            "ok": bool(backup_ok and checksum_result and checksum_result["returncode"] == 0),
            "detail": {
                "latest_backup": str(latest_backup) if latest_backup else None,
                "checksum_result": checksum_result,
            },
        }
    )

    latest_restore = _latest_dir(restore_root)
    restore_checks = []
    if latest_restore:
        for rel_path in config["required_restore_files"]:
            restore_checks.append(
                {
                    "path": str(latest_restore / rel_path),
                    "required": True,
                    "exists": (latest_restore / rel_path).exists(),
                }
            )
        for rel_path in config.get("optional_restore_files", []):
            restore_checks.append(
                {
                    "path": str(latest_restore / rel_path),
                    "required": False,
                    "exists": (latest_restore / rel_path).exists(),
                }
            )
    checks.append(
        {
            "name": "restore_test_files_present",
            "ok": bool(
                latest_restore
                and all(item["exists"] for item in restore_checks if item["required"])
            ),
            "detail": {
                "latest_restore": str(latest_restore) if latest_restore else None,
                "files": restore_checks,
            },
        }
    )

    compose_command = ["docker", "compose"]
    for rel_path in config["compose_files"]:
        compose_command.extend(["-f", rel_path])
    compose_command.extend(["config"])
    compose_result = _run(compose_command, compose_dir, capture_output=False)
    if compose_result["returncode"] == 0:
        rendered_compose_path.write_text(
            "# Render succeeded. Output intentionally suppressed because compose config contains secrets.\n",
            encoding="utf-8",
        )
    checks.append(
        {
            "name": "compose_config_render",
            "ok": compose_result["returncode"] == 0 and rendered_compose_path.exists(),
            "detail": {
                "rendered_compose_path": str(rendered_compose_path),
                "compose_result": compose_result,
            },
        }
    )

    report = {
        "ok": all(check["ok"] for check in checks),
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": str(config_path),
        "mode": "non_destructive",
        "production_restore_performed": False,
        "production_data_deleted": False,
        "checks": checks,
    }

    output_path = Path(config["generated_report"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V1.7F rollback drill.")
    parser.add_argument(
        "--config",
        default="configs/rollback_drill_v1_7F.json",
        help="JSON rollback-drill config path.",
    )
    args = parser.parse_args()

    report = run(Path(args.config))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
