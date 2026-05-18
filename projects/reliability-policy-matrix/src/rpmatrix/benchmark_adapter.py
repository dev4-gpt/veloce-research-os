from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class BenchmarkTask:
    task_id: str
    source: str
    title: str
    instruction: str
    metadata: dict[str, Any]


class BenchmarkAdapter(Protocol):
    name: str

    def load_tasks(self) -> list[BenchmarkTask]:
        """Load tasks for one benchmark slice."""


class JsonlManifestAdapter:
    name = "jsonl_manifest"

    def __init__(self, manifest_path: str | Path, source: str) -> None:
        self.manifest_path = Path(manifest_path)
        self.source = source

    def load_tasks(self) -> list[BenchmarkTask]:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")

        tasks: list[BenchmarkTask] = []
        for line_number, raw_line in enumerate(self.manifest_path.read_text().splitlines(), start=1):
            if not raw_line.strip():
                continue
            payload = json.loads(raw_line)
            task_id = str(payload.get("task_id") or payload.get("id") or f"{self.source}-{line_number}")
            tasks.append(
                BenchmarkTask(
                    task_id=task_id,
                    source=self.source,
                    title=str(payload.get("title") or task_id),
                    instruction=str(payload.get("instruction") or payload.get("goal") or ""),
                    metadata={key: value for key, value in payload.items() if key not in {"task_id", "id", "title", "instruction", "goal"}},
                )
            )
        return tasks


class OSWorldAdapter(JsonlManifestAdapter):
    name = "osworld"

    def __init__(self, manifest_path: str | Path = "manifests/osworld_subset.jsonl") -> None:
        super().__init__(manifest_path=manifest_path, source="osworld_subset")


def adapter_for_benchmark(benchmark: str) -> BenchmarkAdapter:
    manifest_path = Path("manifests") / f"{benchmark}.jsonl"
    if benchmark == "osworld_subset":
        return OSWorldAdapter(manifest_path)
    return JsonlManifestAdapter(manifest_path=manifest_path, source=benchmark)
