#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
THREESTUDIO_ROOT="${PROJECT_ROOT}/external/threestudio"
CONDA_BIN="${CONDA_BIN:-${HOME}/miniforge3/bin/conda}"
THREESTUDIO_ENV="${THREESTUDIO_ENV:-cv_hw3_threestudio}"
GPU="${GPU:-0}"
RUN_NAME="${RUN_NAME:-object-b-dreamfusion-sd-full}"
TRAIN_TAG="${TRAIN_TAG:-full}"
EXPORT_TAG="${EXPORT_TAG:-export}"
EXPORT_RUN_NAME="${EXPORT_RUN_NAME:-${RUN_NAME}-export}"
PROMPT="${PROMPT:-A studio product photo of a small red ceramic teapot with a round body, short spout, and curved handle}"
SD_MODEL="${SD_MODEL:-stable-diffusion-v1-5/stable-diffusion-v1-5}"
ISOSURFACE_THRESHOLD="${ISOSURFACE_THRESHOLD:-25.0}"
OUTPUT_ROOT="${PROJECT_ROOT}/outputs/object_b_text3d/${RUN_NAME}"

source "${SCRIPT_DIR}/configure_aigc_cache_env.sh"

if [[ -z "${TRIAL_DIR:-}" ]]; then
  TRIAL_DIR="$(
    find "${OUTPUT_ROOT}/${RUN_NAME}" \
      -mindepth 1 \
      -maxdepth 1 \
      -type d \
      -name "${TRAIN_TAG}@*" \
      -print 2>/dev/null |
      sort |
      tail -n 1
  )"
fi

if [[ -z "${TRIAL_DIR}" ]]; then
  echo "Could not find a ${TRAIN_TAG} trial under ${OUTPUT_ROOT}/${RUN_NAME}" >&2
  exit 1
fi

CKPT="${CKPT:-${TRIAL_DIR}/ckpts/last.ckpt}"
if [[ ! -f "${CKPT}" ]]; then
  echo "Checkpoint not found: ${CKPT}" >&2
  exit 1
fi

cd -- "${THREESTUDIO_ROOT}"
CUDA_VISIBLE_DEVICES="${GPU}" "${CONDA_BIN}" run -n "${THREESTUDIO_ENV}" --no-capture-output \
  python "${PROJECT_ROOT}/scripts/run_tracked_experiment.py" \
  --stage object_b_text3d_export \
  --run-name "${EXPORT_RUN_NAME}" \
  --cwd "${THREESTUDIO_ROOT}" \
  --output "${OUTPUT_ROOT}" \
  --metric-prefix threestudio_export \
  --config "train_run_name=${RUN_NAME}" \
  --config "train_tag=${TRAIN_TAG}" \
  --config "checkpoint=${CKPT}" \
  --config "prompt=${PROMPT}" \
  --config "sd_model=${SD_MODEL}" \
  --config "isosurface_threshold=${ISOSURFACE_THRESHOLD}" \
  --swanlab-mode "${SWANLAB_MODE:-local}" \
  -- python launch.py \
  --config configs/dreamfusion-sd.yaml \
  --export \
  --gpu 0 \
  "resume=${CKPT}" \
  "system.prompt_processor.prompt=${PROMPT}" \
  "system.prompt_processor.pretrained_model_name_or_path=${SD_MODEL}" \
  "system.guidance.pretrained_model_name_or_path=${SD_MODEL}" \
  "system.exporter_type=mesh-exporter" \
  "system.exporter.fmt=obj" \
  "system.exporter.save_uv=false" \
  "system.exporter.context_type=cuda" \
  "system.geometry.isosurface_threshold=${ISOSURFACE_THRESHOLD}" \
  "exp_root_dir=${OUTPUT_ROOT}" \
  "name=${RUN_NAME}" \
  "tag=${EXPORT_TAG}"
