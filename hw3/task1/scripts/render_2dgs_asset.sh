#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/render_2dgs_asset.sh <model-dir> [iteration]"
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
  --skip_test \
  --skip_mesh
