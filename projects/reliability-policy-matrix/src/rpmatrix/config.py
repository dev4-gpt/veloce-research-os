from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MatrixConfig:
    name: str
    benchmarks: list[str]
    policies: list[str]
    seeds: list[int]
    budget: dict[str, int]
    output_dir: Path


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value.isdigit():
        return int(value)
    return value.strip('"').strip("'")


def _load_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse the limited YAML shape used by this scaffold.

    The project keeps configs intentionally small: top-level scalars, top-level
    lists, and one-level dictionaries such as budget. This avoids requiring a
    package install before a new user can run the first smoke test.
    """
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in path.read_text().splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            if value.strip():
                data[current_key] = _parse_scalar(value)
            else:
                data[current_key] = []
            continue
        if current_key is None:
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            if not isinstance(data[current_key], list):
                data[current_key] = []
            data[current_key].append(_parse_scalar(stripped[2:]))
            continue
        if ":" in stripped:
            if not isinstance(data[current_key], dict):
                data[current_key] = {}
            key, value = stripped.split(":", 1)
            data[current_key][key.strip()] = _parse_scalar(value)
    return data


def load_matrix_config(path: str | Path) -> MatrixConfig:
    config_path = Path(path)
    data = _load_simple_yaml(config_path)

    return MatrixConfig(
        name=str(data["name"]),
        benchmarks=list(data["benchmarks"]),
        policies=list(data["policies"]),
        seeds=[int(seed) for seed in data["seeds"]],
        budget={key: int(value) for key, value in data["budget"].items()},
        output_dir=Path(data.get("output_dir", "artifacts/raw")),
    )


def expand_conditions(config: MatrixConfig) -> list[dict[str, Any]]:
    conditions: list[dict[str, Any]] = []
    for benchmark in config.benchmarks:
        for policy in config.policies:
            for seed in config.seeds:
                conditions.append(
                    {
                        "matrix": config.name,
                        "benchmark": benchmark,
                        "policy": policy,
                        "seed": seed,
                        "budget": config.budget,
                    }
                )
    return conditions
