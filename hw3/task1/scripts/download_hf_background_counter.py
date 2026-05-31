#!/usr/bin/env python3
"""Download only the Mip-NeRF 360 counter scene from a Hugging Face mirror."""

from pathlib import Path

from huggingface_hub import snapshot_download


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data/raw/mipnerf360"
SCENE_DIR = RAW_DIR / "counter"
PROCESSED_LINK = PROJECT_ROOT / "data/processed/background_counter"


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_LINK.parent.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id="nvs-bench/mipnerf360",
        repo_type="dataset",
        allow_patterns=["counter/**"],
        local_dir=RAW_DIR,
        max_workers=8,
    )
    if not (SCENE_DIR / "images").is_dir() or not (SCENE_DIR / "sparse/0").is_dir():
        raise RuntimeError(f"Incomplete counter scene: {SCENE_DIR}")
    if PROCESSED_LINK.is_symlink():
        PROCESSED_LINK.unlink()
    elif PROCESSED_LINK.exists():
        raise RuntimeError(f"Refusing to replace non-symlink path: {PROCESSED_LINK}")
    PROCESSED_LINK.symlink_to(SCENE_DIR, target_is_directory=True)
    print(f"Background scene ready: {PROCESSED_LINK} -> {SCENE_DIR}")


if __name__ == "__main__":
    main()
