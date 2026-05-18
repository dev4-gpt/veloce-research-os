#!/usr/bin/env python
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rpmatrix.config import expand_conditions, load_matrix_config


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def deterministic_score(condition: dict[str, Any]) -> float:
    payload = json.dumps(condition, sort_keys=True).encode()
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/matrix.base.yaml")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    config = load_matrix_config(args.config)
    conditions = expand_conditions(config)
    if args.limit:
        conditions = conditions[: args.limit]

    config.output_dir.mkdir(parents=True, exist_ok=True)
    sha = git_sha()

    for index, condition in enumerate(conditions, start=1):
        score = deterministic_score(condition)
        completed = score >= 0.35
        critical_failure = score < 0.12
        run_id = f"{condition['matrix']}-{index:04d}-{condition['policy']}-{condition['seed']}"
        record = {
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "git_sha": sha,
            **condition,
            "outcome": {
                "completed": completed,
                "success_under_budget": completed and score >= 0.5,
                "critical_failure": critical_failure,
                "steps": int(3 + score * condition["budget"]["max_steps"]),
                "score": round(score, 4),
            },
        }
        out_path = config.output_dir / f"{run_id}.json"
        out_path.write_text(json.dumps(record, indent=2) + "\n")
        print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
