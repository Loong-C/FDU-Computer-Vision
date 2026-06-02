from __future__ import annotations

import sys
from pathlib import Path


def ensure_lerobot_importable() -> None:
    """Use an installed LeRobot package or the pinned local checkout."""
    try:
        import lerobot  # noqa: F401

        return
    except ImportError:
        repo_root = Path(__file__).resolve().parents[2]
        checkout_src = repo_root / "external" / "lerobot" / "src"
        if checkout_src.exists():
            sys.path.insert(0, str(checkout_src))
            return
        raise RuntimeError(
            "LeRobot is not importable. Run scripts/bootstrap.ps1 first or install lerobot==0.5.1."
        )
