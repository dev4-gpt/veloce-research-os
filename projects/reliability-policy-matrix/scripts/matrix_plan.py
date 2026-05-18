#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rpmatrix.config import expand_conditions, load_matrix_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/matrix.base.yaml")
    args = parser.parse_args()

    config = load_matrix_config(args.config)
    conditions = expand_conditions(config)

    print(json.dumps({"config": config.name, "conditions": conditions}, indent=2))


if __name__ == "__main__":
    main()
