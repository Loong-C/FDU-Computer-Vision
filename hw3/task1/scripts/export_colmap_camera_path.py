#!/usr/bin/env python3
"""Export COLMAP binary cameras as Blender-compatible camera matrices."""

import argparse
import json
import math
import struct
from pathlib import Path


CAMERA_MODEL_PARAMS = {
    0: 3,   # SIMPLE_PINHOLE
    1: 4,   # PINHOLE
    2: 4,   # SIMPLE_RADIAL
    3: 5,   # RADIAL
    4: 8,   # OPENCV
    5: 8,   # OPENCV_FISHEYE
    6: 12,  # FULL_OPENCV
    7: 5,   # FOV
    8: 4,   # SIMPLE_RADIAL_FISHEYE
    9: 5,   # RADIAL_FISHEYE
    10: 12, # THIN_PRISM_FISHEYE
}


def read_bytes(handle, size, pattern):
    return struct.unpack("<" + pattern, handle.read(size))


def qvec_to_rotation(qvec):
    w, x, y, z = qvec
    return [
        [1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * w * z, 2 * z * x + 2 * w * y],
        [2 * x * y + 2 * w * z, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * w * x],
        [2 * z * x - 2 * w * y, 2 * y * z + 2 * w * x, 1 - 2 * x * x - 2 * y * y],
    ]


def transpose(matrix):
    return [list(row) for row in zip(*matrix)]


def matrix_vector(matrix, vector):
    return [sum(row[index] * vector[index] for index in range(3)) for row in matrix]


def read_cameras(path):
    cameras = {}
    with path.open("rb") as handle:
        count = read_bytes(handle, 8, "Q")[0]
        for _ in range(count):
            camera_id, model_id, width, height = read_bytes(handle, 24, "iiQQ")
            params = read_bytes(handle, 8 * CAMERA_MODEL_PARAMS[model_id], "d" * CAMERA_MODEL_PARAMS[model_id])
            focal_x = params[0]
            cameras[camera_id] = {
                "angle_x_radians": 2.0 * math.atan(width / (2.0 * focal_x)),
                "height": height,
                "width": width,
            }
    return cameras


def read_images(path, cameras):
    frames = []
    with path.open("rb") as handle:
        count = read_bytes(handle, 8, "Q")[0]
        for _ in range(count):
            image_id, *values = read_bytes(handle, 64, "idddddddi")
            qvec = values[:4]
            tvec = values[4:7]
            camera_id = values[7]
            name_bytes = bytearray()
            while True:
                character = handle.read(1)
                if character == b"\x00":
                    break
                name_bytes.extend(character)
            points_count = read_bytes(handle, 8, "Q")[0]
            handle.seek(24 * points_count, 1)

            world_to_camera = qvec_to_rotation(qvec)
            camera_to_world = transpose(world_to_camera)
            location = [-value for value in matrix_vector(camera_to_world, tvec)]
            # COLMAP uses +Y down and +Z forward; Blender cameras use +Y up and -Z forward.
            rotation = [
                [camera_to_world[row][0], -camera_to_world[row][1], -camera_to_world[row][2]]
                for row in range(3)
            ]
            matrix_world = [
                [rotation[0][0], rotation[0][1], rotation[0][2], location[0]],
                [rotation[1][0], rotation[1][1], rotation[1][2], location[1]],
                [rotation[2][0], rotation[2][1], rotation[2][2], location[2]],
                [0.0, 0.0, 0.0, 1.0],
            ]
            frames.append(
                {
                    "angle_x_radians": cameras[camera_id]["angle_x_radians"],
                    "image_id": image_id,
                    "matrix_world": matrix_world,
                    "name": name_bytes.decode("utf-8"),
                }
            )
    return sorted(frames, key=lambda frame: frame["name"])


def vector_summary(frames):
    locations = [[row[3] for row in frame["matrix_world"][:3]] for frame in frames]
    return {
        "count": len(frames),
        "location_minimum": [min(location[index] for location in locations) for index in range(3)],
        "location_maximum": [max(location[index] for location in locations) for index in range(3)],
        "location_mean": [
            sum(location[index] for location in locations) / len(locations)
            for index in range(3)
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images-bin", required=True, type=Path)
    parser.add_argument("--cameras-bin", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    frames = read_images(args.images_bin, read_cameras(args.cameras_bin))
    payload = {
        "source_images_bin": str(args.images_bin),
        "summary": vector_summary(frames),
        "frames": frames,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
