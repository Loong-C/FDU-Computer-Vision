#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
CONDA_BIN="${CONDA_BIN:-/home/hp/miniforge3/bin/conda}"
SWANLAB_MODE="${SWANLAB_MODE:-local}"
MODE="${MODE:-formal}"

case "${MODE}" in
  smoke)
    FUSION_CONFIG="${FUSION_CONFIG:-${PROJECT_ROOT}/configs/fusion_scene_smoke.json}"
    OUTPUT_DIR="${PROJECT_ROOT}/outputs/fusion_smoke"
    DEFAULT_RUN_NAME="task1-fusion-smoke"
    ;;
  formal)
    FUSION_CONFIG="${FUSION_CONFIG:-${PROJECT_ROOT}/configs/fusion_scene.json}"
    OUTPUT_DIR="${PROJECT_ROOT}/outputs/fusion"
    DEFAULT_RUN_NAME="task1-fusion-render"
    ;;
  *)
    echo "Unsupported MODE=${MODE}; expected smoke or formal." >&2
    exit 2
    ;;
esac
RUN_NAME="${RUN_NAME:-${DEFAULT_RUN_NAME}}"

"${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
  python "${PROJECT_ROOT}/scripts/run_tracked_experiment.py" \
  --stage fusion_render \
  --run-name "${RUN_NAME}" \
  --cwd "${PROJECT_ROOT}" \
  --output "${OUTPUT_DIR}" \
  --metric-prefix fusion \
  --config "mode=${MODE}" \
  --config "config=${FUSION_CONFIG}" \
  --swanlab-mode "${SWANLAB_MODE}" \
  -- \
  env "FUSION_CONFIG=${FUSION_CONFIG}" bash scripts/render_fusion.sh
