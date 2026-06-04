from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from hw3_calvin_act.calvin_rollout import run_rollout_cli


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deploy a trained ACT checkpoint in the CALVIN D simulator and evaluate zero-shot rollout success."
    )
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "configs" / "calvin_act.yaml")
    parser.add_argument("--dataset-root", type=Path, required=True, help="Path to task_D_D.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--device")
    parser.add_argument("--max-sequences", type=int, default=10)
    parser.add_argument("--ep-len", type=int, default=360)
    parser.add_argument("--scene", default="calvin_scene_D")
    parser.add_argument("--use-egl", action="store_true", help="Use PyBullet EGL rendering instead of DIRECT mode.")
    parser.add_argument("--check-only", action="store_true", help="Only verify dependencies/config without rollout.")
    args = parser.parse_args()
    raise SystemExit(run_rollout_cli(args))


if __name__ == "__main__":
    main()
