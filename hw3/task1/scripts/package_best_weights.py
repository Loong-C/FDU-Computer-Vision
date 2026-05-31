#!/usr/bin/env python3
"""Package Task 1 best weights and exported meshes for public download."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parents[1]
DEFAULT_RELEASE_DIR = Path("/mnt/d/PackageCache/cv-hw3-task1-release")
PACKAGE_NAME = "cv-hw3-task1-best-weights"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def latest_match(pattern: str) -> Path:
    matches = sorted(PROJECT_ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No files match {pattern}")
    return matches[-1]


def verify_release_dir(path: Path) -> Path:
    resolved = path.resolve()
    package_cache = Path("/mnt/d/PackageCache").resolve()
    if package_cache not in resolved.parents:
        raise RuntimeError(f"Release directory must stay under {package_cache}: {resolved}")
    return resolved


def copy_artifact(source: Path, staging: Path, relative_path: str) -> dict[str, object]:
    if not source.is_file() or source.stat().st_size == 0:
        raise FileNotFoundError(source)
    destination = staging / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "path": relative_path,
        "source": str(source.relative_to(PROJECT_ROOT)),
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", type=Path, default=DEFAULT_RELEASE_DIR)
    parser.add_argument(
        "--object-c-fine-root",
        type=Path,
        default=Path("outputs/object_c_magic123/object-c-magic123-fine-full"),
    )
    parser.add_argument(
        "--metadata-output",
        type=Path,
        default=Path("logs/task1-best-weights-package.json"),
    )
    args = parser.parse_args()

    release_dir = verify_release_dir(args.release_dir)
    fine_root = args.object_c_fine_root
    if not fine_root.is_absolute():
        fine_root = PROJECT_ROOT / fine_root
    metadata_output = args.metadata_output
    if not metadata_output.is_absolute():
        metadata_output = PROJECT_ROOT / metadata_output
    staging = release_dir / PACKAGE_NAME
    archive = release_dir / f"{PACKAGE_NAME}.tar.gz"
    manifest_path = release_dir / f"{PACKAGE_NAME}.manifest.json"
    release_notes_path = release_dir / "release-notes.md"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    release_dir.mkdir(parents=True, exist_ok=True)

    sources = [
        (
            PROJECT_ROOT / "outputs/object_a_2dgs/object-a-2dgs-full/point_cloud/iteration_30000/point_cloud.ply",
            "object_a_2dgs/iteration_30000/point_cloud.ply",
        ),
        (
            PROJECT_ROOT / "outputs/background_2dgs/background-counter-2dgs-full/point_cloud/iteration_30000/point_cloud.ply",
            "background_counter_2dgs/iteration_30000/point_cloud.ply",
        ),
        (
            latest_match("outputs/object_b_text3d/object-b-dreamfusion-sd-full/**/*.obj"),
            "object_b_dreamfusion/model.obj",
        ),
        (
            PROJECT_ROOT / "outputs/object_c_magic123/object-c-magic123-coarse-full/checkpoints/object-c-magic123-coarse-full.pth",
            "object_c_magic123/coarse/object-c-magic123-coarse-full.pth",
        ),
        (
            fine_root / "checkpoints" / f"{fine_root.name}.pth",
            "object_c_magic123/fine/object-c-magic123-fine-full.pth",
        ),
        (
            fine_root / "mesh/mesh.obj",
            "object_c_magic123/fine/mesh/mesh.obj",
        ),
        (
            fine_root / "mesh/mesh.mtl",
            "object_c_magic123/fine/mesh/mesh.mtl",
        ),
        (
            fine_root / "mesh/albedo.png",
            "object_c_magic123/fine/mesh/albedo.png",
        ),
    ]
    artifacts = [copy_artifact(source, staging, relative_path) for source, relative_path in sources]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    manifest = {
        "package": PACKAGE_NAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": commit,
        "artifacts": artifacts,
    }
    staged_manifest = staging / "manifest.json"
    staged_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    release_notes_path.write_text(
        "# CV HW3 Task 1 best weights\n\n"
        "Public download package for the `hw3` branch. It contains the formal "
        "Object A and counter-background 2DGS point clouds, the formal Object B "
        "DreamFusion OBJ, and the formal Object C Magic123 coarse/fine checkpoints "
        "plus textured mesh. See `manifest.json` inside the archive for SHA-256 "
        "checksums of each artifact.\n",
        encoding="utf-8",
    )
    with tarfile.open(archive, "w:gz") as handle:
        handle.add(staging, arcname=PACKAGE_NAME)
    archive_sha256 = sha256(archive)
    checksum_path = archive.with_suffix(archive.suffix + ".sha256")
    checksum_path.write_text(f"{archive_sha256}  {archive.name}\n", encoding="utf-8")
    metadata = {
        **manifest,
        "archive": str(archive),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": archive_sha256,
        "checksum": str(checksum_path),
    }
    metadata_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
