#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
THREESTUDIO_ROOT="${PROJECT_ROOT}/external/threestudio"
CONDA_BIN="${CONDA_BIN:-${HOME}/miniforge3/bin/conda}"
THREESTUDIO_ENV="${THREESTUDIO_ENV:-cv_hw3_threestudio}"
MODE="${MODE:-smoke}"
GPU="${GPU:-0}"
PROMPT="${PROMPT:-A studio product photo of a small red ceramic teapot with a round body, short spout, and curved handle}"
SD_MODEL="${SD_MODEL:-stable-diffusion-v1-5/stable-diffusion-v1-5}"

if [[ -d /mnt/d ]]; then
  export HF_HOME="${HF_HOME:-/mnt/d/PackageCache/wsl/huggingface}"
  mkdir -p -- "${HF_HOME}"
fi
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

case "${MODE}" in
  smoke)
    STEPS="${STEPS:-20}"
    WIDTH="${WIDTH:-32}"
    HEIGHT="${HEIGHT:-32}"
    VAL_INTERVAL="${VAL_INTERVAL:-20}"
    ;;
  full)
    STEPS="${STEPS:-10000}"
    WIDTH="${WIDTH:-64}"
    HEIGHT="${HEIGHT:-64}"
    VAL_INTERVAL="${VAL_INTERVAL:-200}"
    ;;
  *)
    echo "MODE must be smoke or full" >&2
    exit 2
    ;;
esac

RUN_NAME="${RUN_NAME:-object-b-dreamfusion-sd-${MODE}}"
OUTPUT_ROOT="${PROJECT_ROOT}/outputs/object_b_text3d/${RUN_NAME}"

cd -- "${THREESTUDIO_ROOT}"
CUDA_VISIBLE_DEVICES="${GPU}" "${CONDA_BIN}" run -n "${THREESTUDIO_ENV}" --no-capture-output \
  python "${PROJECT_ROOT}/scripts/run_tracked_experiment.py" \
  --stage object_b_text3d \
  --run-name "${RUN_NAME}" \
  --cwd "${THREESTUDIO_ROOT}" \
  --output "${OUTPUT_ROOT}" \
  --metric-prefix threestudio \
  --config "mode=${MODE}" \
  --config "iterations=${STEPS}" \
  --config "width=${WIDTH}" \
  --config "height=${HEIGHT}" \
  --config "prompt=${PROMPT}" \
  --config "sd_model=${SD_MODEL}" \
  --swanlab-mode "${SWANLAB_MODE:-local}" \
  -- python launch.py \
  --config configs/dreamfusion-sd.yaml \
  --train \
  --gpu 0 \
  "system.prompt_processor.prompt=${PROMPT}" \
  "system.prompt_processor.pretrained_model_name_or_path=${SD_MODEL}" \
  "system.guidance.pretrained_model_name_or_path=${SD_MODEL}" \
  "exp_root_dir=${OUTPUT_ROOT}" \
  "name=${RUN_NAME}" \
  "tag=${MODE}" \
  "trainer.max_steps=${STEPS}" \
  "trainer.val_check_interval=${VAL_INTERVAL}" \
  "data.width=${WIDTH}" \
  "data.height=${HEIGHT}"
