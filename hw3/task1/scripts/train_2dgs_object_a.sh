#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

python "${PROJECT_ROOT}/scripts/run_2dgs_experiment.py" \
  --stage object_a_2dgs \
  --run-name "${RUN_NAME:-object-a-2dgs-full}" \
  --source "${PROJECT_ROOT}/data/processed/object_a_2dgs_ready" \
  --output "${PROJECT_ROOT}/outputs/object_a_2dgs/${RUN_NAME:-object-a-2dgs-full}" \
  --iterations "${ITERATIONS:-30000}" \
  --resolution "${RESOLUTION:--1}" \
  --test-iterations "${TEST_ITERATIONS:-7000,30000}" \
  --save-iterations "${SAVE_ITERATIONS:-7000,30000}" \
  --depth-ratio "${DEPTH_RATIO:-0.0}" \
  --lambda-normal "${LAMBDA_NORMAL:-0.05}" \
  --lambda-distortion "${LAMBDA_DISTORTION:-0.0}" \
  "$@"
