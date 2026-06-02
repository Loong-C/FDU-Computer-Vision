from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


ENVIRONMENT_OFFSETS = {
    "A": 0.0,
    "B": 0.2,
    "C": -0.2,
    "D": 0.45,
}


def make_image(environment: str, step: int, height: int, width: int) -> np.ndarray:
    base_colors = {
        "A": (160, 55, 45),
        "B": (45, 155, 75),
        "C": (50, 80, 175),
        "D": (175, 145, 40),
    }
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, :] = base_colors[environment]
    x = step % max(width - 8, 1)
    y = (step * 3) % max(height - 8, 1)
    image[y : y + 8, x : x + 8] = (235, 235, 235)
    return image


def write_scene(
    split_root: Path,
    environment: str,
    start_index: int,
    frames: int,
    rng: np.random.Generator,
) -> tuple[int, int]:
    split_root.mkdir(parents=True, exist_ok=True)
    offset = ENVIRONMENT_OFFSETS[environment]
    for local_step in range(frames):
        frame_index = start_index + local_step
        phase = local_step / max(frames - 1, 1)
        robot_obs = np.linspace(-0.4, 0.4, 15, dtype=np.float32)
        robot_obs += offset + 0.05 * np.sin(phase * np.pi * 2)
        robot_obs += rng.normal(0.0, 0.01, size=15).astype(np.float32)
        rel_actions = np.asarray(
            [
                0.30 * np.sin(phase * np.pi * 2) + offset,
                0.20 * np.cos(phase * np.pi * 2) - offset,
                0.10 + offset,
                0.05 * np.sin(phase * np.pi),
                0.05 * np.cos(phase * np.pi),
                0.02 * np.sin(phase * np.pi * 4),
                1.0 if local_step % 6 < 3 else -1.0,
            ],
            dtype=np.float32,
        )
        np.savez_compressed(
            split_root / f"episode_{frame_index:07d}.npz",
            rgb_static=make_image(environment, local_step, 96, 96),
            rgb_gripper=make_image(environment, local_step, 84, 84),
            robot_obs=robot_obs,
            rel_actions=rel_actions,
            actions=rel_actions,
            scene_obs=np.full(24, offset, dtype=np.float32),
        )
    return start_index, start_index + frames - 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a tiny CALVIN-shaped dataset for local smoke tests.")
    parser.add_argument("--output-root", type=Path, default=Path("data/smoke"))
    parser.add_argument("--frames-per-env", type=int, default=18)
    parser.add_argument("--seed", type=int, default=123)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    abc_root = args.output_root / "task_ABC_D" / "training"
    d_root = args.output_root / "task_D_D" / "validation"

    scene_info = {}
    frame_index = 0
    for environment in "BCA":
        start, end = write_scene(abc_root, environment, frame_index, args.frames_per_env, rng)
        scene_info[f"calvin_scene_{environment}"] = [start, end]
        frame_index = end + 1
    np.save(abc_root / "scene_info.npy", scene_info)

    start, end = write_scene(d_root, "D", 0, args.frames_per_env, rng)
    np.save(d_root / "scene_info.npy", {"calvin_scene_D": [start, end]})
    print(f"Generated ABC smoke data under {abc_root}")
    print(f"Generated D smoke data under {d_root}")


if __name__ == "__main__":
    main()
