#!/usr/bin/env python3
"""Fill final report metadata after Object C, fusion, and cloud upload finish."""

from __future__ import annotations

import argparse
import datetime
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def elapsed_seconds(run_name: str) -> float:
    path = PROJECT_ROOT / "logs" / f"{run_name}.json"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    if metadata.get("exit_code") != 0:
        raise RuntimeError(f"Run did not finish successfully: {path}")
    return round(float(metadata["elapsed_seconds"]), 4)


def replace_once(text: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Expected one match for pattern: {pattern}")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cloud-weights-url", required=True)
    parser.add_argument("--public-walkthrough-url", required=True)
    parser.add_argument("--fusion-run-name", default="task1-fusion-render")
    args = parser.parse_args()

    paths = {
        "formal_mesh": "outputs/object_c_magic123/object-c-magic123-fine-full/mesh/mesh.obj",
        "object_c_preview": "docs/figures/object_c_magic123_final_preview.jpg",
        "fusion_video": "outputs/fusion/task1-walkthrough.mp4",
        "fusion_preview": "docs/figures/fusion_walkthrough_preview.png",
    }
    for path in paths.values():
        full_path = PROJECT_ROOT / path
        if not full_path.is_file() or full_path.stat().st_size == 0:
            raise FileNotFoundError(full_path)

    coarse = elapsed_seconds("object-c-magic123-coarse-full")
    fine = elapsed_seconds("object-c-magic123-fine-full")
    fusion = elapsed_seconds(args.fusion_run_name)
    report_data_path = PROJECT_ROOT / "report/report_data.json"
    data = json.loads(report_data_path.read_text(encoding="utf-8"))
    data.update(
        {
            "status": "final",
            "generated_on": datetime.datetime.now().astimezone().date().isoformat(),
            "cloud_weights_url": args.cloud_weights_url,
            "object_c": {
                "formal_mesh": paths["formal_mesh"],
                "preview": paths["object_c_preview"],
                "coarse_seconds": coarse,
                "fine_seconds": fine,
            },
            "fusion": {
                "video": paths["fusion_video"],
                "public_video_url": args.public_walkthrough_url,
                "preview": paths["fusion_preview"],
                "render_seconds": fusion,
            },
        }
    )
    report_data_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    time_cost_path = PROJECT_ROOT / "notes/time_cost.md"
    time_cost = time_cost_path.read_text(encoding="utf-8")
    time_cost = replace_once(
        time_cost,
        r"^\| Object C \| Magic123 \|.*$",
        f"| Object C | Magic123 | Local CUDA GPU | 500 local-formal coarse + 500 local-formal fine iterations (`5000 + 5000` official reference) | {coarse:.2f} s coarse + {fine:.2f} s fine | SD + Zero123 coarse NeRF and fine DMTet; local budget adapted after measured 75.18 s guided steps |",
    )
    fusion_row = (
        f"| Fusion | Blender | Local CPU | 180 frames / 640 x 480 | {fusion:.2f} s | "
        "COLMAP-path walkthrough with unified textured meshes and multi-direction fill lighting |"
    )
    if "| Fusion | Blender |" in time_cost:
        time_cost = replace_once(
            time_cost,
            r"^\| Fusion \| Blender \|.*$",
            fusion_row,
        )
    else:
        if time_cost and not time_cost.endswith("\n"):
            time_cost += "\n"
        time_cost += fusion_row + "\n"
    time_cost_path.write_text(time_cost, encoding="utf-8")

    outline_path = PROJECT_ROOT / "notes/report_outline.md"
    outline = outline_path.read_text(encoding="utf-8")
    outline = outline.replace("| Object C | PENDING | PENDING | PENDING |", f"| Object C | `{paths['formal_mesh']}` | `{paths['object_c_preview']}` | {coarse:.2f} s coarse + {fine:.2f} s fine |")
    outline = replace_once(
        outline,
        r"^\| Fusion \| unified scene \|.*$",
        f"| Fusion | unified scene | `{paths['fusion_video']}` | {fusion:.2f} s |",
    )
    outline = outline.replace("- Best model weights cloud link: `PENDING`", f"- Best model weights cloud link: `{args.cloud_weights_url}`")
    outline = outline.replace("- Public walkthrough video link: `PENDING`", f"- Public walkthrough video link: `{args.public_walkthrough_url}`")
    outline_path.write_text(outline, encoding="utf-8")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
