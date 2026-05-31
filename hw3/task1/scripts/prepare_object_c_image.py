#!/usr/bin/env python3
"""Remove a baked checkerboard background and prepare an RGBA Magic123 input."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import swanlab


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checkerboard_convex_hull(image, color_threshold, dark_threshold):
    channel_min = image.min(axis=2)
    channel_max = image.max(axis=2)
    seed_mask = ((channel_max - channel_min) >= color_threshold) | (
        channel_max <= dark_threshold
    )
    points = np.column_stack(np.nonzero(seed_mask))[:, ::-1].astype(np.int32)
    if len(points) < 3:
        raise RuntimeError("Not enough foreground seeds to compute a convex hull")
    hull = cv2.convexHull(points)
    foreground = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(foreground, hull, 255)
    return foreground, len(points), cv2.contourArea(hull)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "data/raw/object_c_image/c.png",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data/processed/object_c_image/c_rgba.png",
    )
    parser.add_argument(
        "--preview",
        type=Path,
        default=PROJECT_ROOT / "docs/figures/object_c_preprocessed_preview.png",
    )
    parser.add_argument("--color-threshold", type=int, default=20)
    parser.add_argument("--dark-threshold", type=int, default=205)
    parser.add_argument("--feather-radius", type=int, default=3)
    parser.add_argument("--swanlab-mode", default="local", choices=["cloud", "local", "disabled"])
    args = parser.parse_args()

    args.input = args.input.resolve()
    args.output = args.output.resolve()
    args.preview = args.preview.resolve()
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.preview.parent.mkdir(parents=True, exist_ok=True)

    image = cv2.imread(str(args.input), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(args.input)
    if image.ndim != 3:
        raise ValueError(f"Expected a color image, got shape {image.shape}")

    original_channels = image.shape[2]
    if original_channels == 4:
        bgr = image[:, :, :3]
        alpha = image[:, :, 3]
        seed_count = 0
        hull_area = 0.0
    elif original_channels == 3:
        bgr = image
        alpha, seed_count, hull_area = checkerboard_convex_hull(
            bgr, args.color_threshold, args.dark_threshold
        )
        if args.feather_radius:
            kernel_size = args.feather_radius * 2 + 1
            alpha = cv2.GaussianBlur(alpha, (kernel_size, kernel_size), 0)
    else:
        raise ValueError(f"Expected RGB or RGBA input, got {original_channels} channels")

    rgba = np.dstack((bgr, alpha))
    cv2.imwrite(str(args.output), rgba)

    alpha_float = alpha.astype(np.float32) / 255.0
    white = np.full_like(bgr, 255)
    preview = (
        bgr.astype(np.float32) * alpha_float[:, :, None]
        + white.astype(np.float32) * (1.0 - alpha_float[:, :, None])
    ).astype(np.uint8)
    cv2.imwrite(str(args.preview), preview)

    foreground_ratio = float(np.mean(alpha > 127))
    metadata = {
        "stage": "object_c_preprocess",
        "method": "checkerboard foreground-seed convex hull",
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "output": str(args.output),
        "preview": str(args.preview),
        "width": int(image.shape[1]),
        "height": int(image.shape[0]),
        "input_channels": int(original_channels),
        "foreground_seed_count": int(seed_count),
        "hull_area": float(hull_area),
        "foreground_ratio": foreground_ratio,
        "color_threshold": args.color_threshold,
        "dark_threshold": args.dark_threshold,
        "feather_radius": args.feather_radius,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    (logs_dir / "object-c-preprocess.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )

    swanlab.init(
        project="cv-hw3-task1",
        experiment_name="object-c-preprocess",
        config=metadata,
        logdir=str(PROJECT_ROOT / "swanlog"),
        mode=args.swanlab_mode,
    )
    swanlab.log(
        {
            "preprocess/width": metadata["width"],
            "preprocess/height": metadata["height"],
            "preprocess/input_channels": metadata["input_channels"],
            "preprocess/foreground_seed_count": metadata["foreground_seed_count"],
            "preprocess/hull_area": metadata["hull_area"],
            "preprocess/foreground_ratio": metadata["foreground_ratio"],
        }
    )
    swanlab.finish()
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
