#!/usr/bin/env python3
"""Report Task 1 data, model, asset, and rendering readiness as JSON."""

import argparse
import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def count_files(path, pattern):
    return len(list(path.glob(pattern))) if path.exists() else 0


def path_check(name, path):
    return {
        "name": name,
        "ready": path.exists(),
        "path": str(path),
        "bytes": path.stat().st_size if path.is_file() else None,
    }


def glob_check(name, root, pattern):
    matches = sorted(str(path) for path in root.glob(pattern)) if root.exists() else []
    return {
        "name": name,
        "ready": bool(matches),
        "path": str(root),
        "pattern": pattern,
        "matches": matches,
    }


def command_check(name, path, *args):
    result = {
        "name": name,
        "ready": False,
        "path": str(path),
    }
    if not path.exists():
        return result
    try:
        process = subprocess.run(
            [str(path), *args],
            capture_output=True,
            check=False,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        result["error"] = str(error)
        return result
    result["ready"] = process.returncode == 0
    result["returncode"] = process.returncode
    result["stdout"] = process.stdout.strip().splitlines()[0] if process.stdout.strip() else ""
    result["stderr"] = process.stderr.strip()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    data = PROJECT_ROOT / "data"
    outputs = PROJECT_ROOT / "outputs"
    magic123 = PROJECT_ROOT / "external" / "Magic123"
    checks = [
        {
            "name": "object_a_colmap_images",
            "ready": count_files(data / "processed/object_a_2dgs_ready/images", "*") > 0,
            "path": str(data / "processed/object_a_2dgs_ready/images"),
            "count": count_files(data / "processed/object_a_2dgs_ready/images", "*"),
        },
        path_check(
            "object_a_2dgs_iteration_7000",
            outputs / "object_a_2dgs/object-a-2dgs-full/point_cloud/iteration_7000/point_cloud.ply",
        ),
        path_check(
            "object_a_2dgs_iteration_30000",
            outputs / "object_a_2dgs/object-a-2dgs-full/point_cloud/iteration_30000/point_cloud.ply",
        ),
        {
            "name": "background_counter_images",
            "ready": count_files(data / "processed/background_counter/images", "*") > 0,
            "path": str(data / "processed/background_counter/images"),
            "count": count_files(data / "processed/background_counter/images", "*"),
        },
        path_check(
            "background_2dgs_iteration_30000",
            outputs / "background_2dgs/background-counter-2dgs-full/point_cloud/iteration_30000/point_cloud.ply",
        ),
        path_check("object_c_rgba", data / "processed/object_c_image/c_rgba.png"),
        path_check("magic123_zero123_weight", magic123 / "pretrained/zero123/105000.ckpt"),
        path_check("magic123_midas_weight", magic123 / "pretrained/midas/dpt_beit_large_512.pt"),
        path_check("object_c_magic123_depth", magic123 / "data/hw3/medicine_box/depth.png"),
        glob_check(
            "object_b_mesh",
            outputs / "object_b_text3d/object-b-dreamfusion-sd-full",
            "**/*.obj",
        ),
        glob_check(
            "object_c_mesh",
            outputs / "object_c_magic123/object-c-magic123-fine-full",
            "**/*.obj",
        ),
        glob_check("fusion_video", outputs / "fusion", "*.mp4"),
        command_check(
            "blender_portable_runtime",
            PROJECT_ROOT / "external/blender/blender",
            "--version",
        ),
    ]
    ready_count = sum(check["ready"] for check in checks)
    summary = {
        "project_root": str(PROJECT_ROOT),
        "ready_count": ready_count,
        "total_count": len(checks),
        "all_ready": ready_count == len(checks),
        "checks": checks,
    }
    text = json.dumps(summary, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if args.strict and not summary["all_ready"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
