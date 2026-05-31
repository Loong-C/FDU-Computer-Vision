#!/usr/bin/env python3
"""Prefetch only the public Stable Diffusion 1.5 files needed by Task 1."""

import argparse
import json
import os

os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "600")

from huggingface_hub import snapshot_download


REQUIRED_PATTERNS = [
    "model_index.json",
    "scheduler/*",
    "text_encoder/config.json",
    "text_encoder/model.safetensors",
    "tokenizer/*",
    "unet/config.json",
    "unet/diffusion_pytorch_model.safetensors",
    "vae/config.json",
    "vae/diffusion_pytorch_model.safetensors",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-id",
        default="stable-diffusion-v1-5/stable-diffusion-v1-5",
    )
    parser.add_argument("--max-workers", type=int, default=1)
    args = parser.parse_args()

    snapshot_path = snapshot_download(
        repo_id=args.repo_id,
        allow_patterns=REQUIRED_PATTERNS,
        max_workers=args.max_workers,
        resume_download=True,
    )
    print(
        json.dumps(
            {
                "repo_id": args.repo_id,
                "snapshot_path": snapshot_path,
                "hf_home": os.environ.get("HF_HOME"),
                "hf_endpoint": os.environ.get("HF_ENDPOINT"),
                "max_workers": args.max_workers,
                "patterns": REQUIRED_PATTERNS,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
