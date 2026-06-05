from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Paths:
    data_root: Path
    output_root: Path
    swanlab_log_dir: Path


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise ValueError(f"Expected a mapping in config file: {path}")
    return config


def resolve_paths() -> Paths:
    repo_root = Path(__file__).resolve().parents[2]
    return Paths(
        data_root=Path(os.getenv("HW3_TASK2_DATA_ROOT", repo_root / "data")),
        output_root=Path(os.getenv("HW3_TASK2_OUTPUT_ROOT", repo_root / "outputs")),
        swanlab_log_dir=Path(os.getenv("SWANLAB_LOG_DIR", repo_root / "swanlog")),
    )
