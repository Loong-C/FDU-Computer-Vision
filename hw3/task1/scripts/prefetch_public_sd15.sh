#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONDA_BIN="${CONDA_BIN:-${HOME}/miniforge3/bin/conda}"
AIGC_ENV="${AIGC_ENV:-cv_hw3_threestudio}"
SD_MODEL="${SD_MODEL:-stable-diffusion-v1-5/stable-diffusion-v1-5}"

source "${SCRIPT_DIR}/configure_aigc_cache_env.sh"

"${CONDA_BIN}" run -n "${AIGC_ENV}" --no-capture-output \
  python "${SCRIPT_DIR}/prefetch_public_sd15.py" \
  --repo-id "${SD_MODEL}" \
  --max-workers "${MAX_WORKERS:-1}"
