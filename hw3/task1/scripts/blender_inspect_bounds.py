"""Inspect imported Task 1 mesh bounds before a Blender fusion render."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from blender_fuse_scene import import_mesh, resolve_asset  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])


def world_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    corners = [
        obj.matrix_world @ Vector(corner)
        for obj in objects
        if obj.type == "MESH"
        for corner in obj.bound_box
    ]
    if not corners:
        raise RuntimeError("Imported asset has no mesh bounds.")
    return (
        Vector(min(corner[index] for corner in corners) for index in range(3)),
        Vector(max(corner[index] for corner in corners) for index in range(3)),
    )


def vector(values: Vector) -> list[float]:
    return [round(value, 6) for value in values]


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    results = []
    for asset in config["assets"]:
        path = resolve_asset(asset)
        objects = import_mesh(path)
        for obj in objects:
            obj.location = asset["location"]
            obj.rotation_euler = [
                value * 3.141592653589793 / 180.0
                for value in asset["rotation_deg"]
            ]
            obj.scale = asset["scale"]
        bpy.context.view_layer.update()
        minimum, maximum = world_bounds(objects)
        results.append(
            {
                "asset": asset["name"],
                "path": str(path),
                "objects": len(objects),
                "minimum": vector(minimum),
                "maximum": vector(maximum),
                "center": vector((minimum + maximum) * 0.5),
                "size": vector(maximum - minimum),
            }
        )

    print("TASK1_BOUNDS_JSON_BEGIN")
    print(json.dumps(results, indent=2))
    print("TASK1_BOUNDS_JSON_END")


if __name__ == "__main__":
    main()
