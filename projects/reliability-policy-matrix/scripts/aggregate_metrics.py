#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="artifacts/raw")
    parser.add_argument("--out", default="artifacts/derived/summary.csv")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for path in sorted(raw_dir.glob("*.json")):
        record = json.loads(path.read_text())
        groups[(record["benchmark"], record["policy"])].append(record)

    rows = []
    for (benchmark, policy), records in sorted(groups.items()):
        total = len(records)
        completed = sum(1 for item in records if item["outcome"]["completed"])
        success_budget = sum(1 for item in records if item["outcome"]["success_under_budget"])
        critical = sum(1 for item in records if item["outcome"]["critical_failure"])
        mean_steps = sum(item["outcome"]["steps"] for item in records) / total if total else 0
        rows.append(
            {
                "benchmark": benchmark,
                "policy": policy,
                "runs": total,
                "completion_rate": round(completed / total, 4) if total else 0,
                "success_under_budget_rate": round(success_budget / total, 4) if total else 0,
                "critical_failure_rate": round(critical / total, 4) if total else 0,
                "mean_steps": round(mean_steps, 2),
            }
        )

    with out_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "benchmark",
                "policy",
                "runs",
                "completion_rate",
                "success_under_budget_rate",
                "critical_failure_rate",
                "mean_steps",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
