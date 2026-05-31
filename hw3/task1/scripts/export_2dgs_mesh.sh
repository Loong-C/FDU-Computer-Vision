#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/export_2dgs_mesh.sh <model-dir> [iteration]"
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
MODEL_DIR="$(realpath -- "$1")"
ITERATION="${2:--1}"

cd "${PROJECT_ROOT}/external/2d-gaussian-splatting"
python render.py \
  --model_path "${MODEL_DIR}" \
  --iteration "${ITERATION}" \
  --skip_train \
  --skip_test \
  --voxel_size "${VOXEL_SIZE:-0.03}" \
  --depth_trunc "${DEPTH_TRUNC:-7.5}" \
  --sdf_trunc "${SDF_TRUNC:-0.15}"
