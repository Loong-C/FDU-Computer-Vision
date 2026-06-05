#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
MAGIC123_ROOT="${PROJECT_ROOT}/external/Magic123"
CONDA_BIN="${CONDA_BIN:-${HOME}/miniforge3/bin/conda}"
MAGIC123_ENV="${MAGIC123_ENV:-cv_hw3_magic123}"
DATA_DIR="${MAGIC123_ROOT}/data/hw3/medicine_box"
MODE="${MODE:-smoke}"
STAGE="${STAGE:-coarse}"
GPU="${GPU:-0}"
TEXT_PROMPT="${TEXT_PROMPT:-A high-resolution DSLR product photo of an amoxicillin capsule medicine box}"
MAGIC123_SD_MODEL="${MAGIC123_SD_MODEL:-stable-diffusion-v1-5/stable-diffusion-v1-5}"

source "${SCRIPT_DIR}/configure_aigc_cache_env.sh"
"${SCRIPT_DIR}/relocate_magic123_clip_cache.sh"
"${SCRIPT_DIR}/apply_magic123_patches.sh"

case "${MODE}" in
  smoke)
    ITERS="${ITERS:-20}"
    WIDTH="${WIDTH:-64}"
    HEIGHT="${HEIGHT:-64}"
    TEST_VIEWS="${TEST_VIEWS:-12}"
    MCUBES_RESOLUTION="${MCUBES_RESOLUTION:-64}"
    ;;
  full)
    ITERS="${ITERS:-500}"
    WIDTH="${WIDTH:-128}"
    HEIGHT="${HEIGHT:-128}"
    TEST_VIEWS="${TEST_VIEWS:-100}"
    MCUBES_RESOLUTION="${MCUBES_RESOLUTION:-192}"
    ;;
  *)
    echo "MODE must be smoke or full" >&2
    exit 2
    ;;
esac

if [[ ! -s "${DATA_DIR}/rgba.png" || ! -s "${DATA_DIR}/depth.png" ]]; then
  echo "Prepare Object C first: bash scripts/prepare_magic123_object_c.sh" >&2
  exit 1
fi

RUN_NAME="${RUN_NAME:-object-c-magic123-${STAGE}-${MODE}}"
WORKSPACE="${PROJECT_ROOT}/outputs/object_c_magic123/${RUN_NAME}"
COMMON_ARGS=(
  python main.py
  -O
  --vram_O
  --text "${TEXT_PROMPT}"
  --sd_version 1.5
  --hf_key "${MAGIC123_SD_MODEL}"
  --image "${DATA_DIR}/rgba.png"
  --workspace "${WORKSPACE}"
  --optim adam
  --iters "${ITERS}"
  --guidance SD zero123
  --guidance_scale 100 5
  --latent_iter_ratio 0
  --bg_radius -1
  --w "${WIDTH}"
  --h "${HEIGHT}"
  --dataset_size_valid 4
  --dataset_size_test "${TEST_VIEWS}"
  --mcubes_resolution "${MCUBES_RESOLUTION}"
  --save_mesh
)

case "${STAGE}" in
  coarse)
    COMMAND=(
      "${COMMON_ARGS[@]}"
      --lambda_guidance 1.0 40
      --normal_iter_ratio 0.2
      --t_range 0.2 0.6
    )
    ;;
  fine)
    COARSE_RUN_NAME="${COARSE_RUN_NAME:-object-c-magic123-coarse-${MODE}}"
    COARSE_WORKSPACE="${PROJECT_ROOT}/outputs/object_c_magic123/${COARSE_RUN_NAME}"
    INIT_CKPT="${COARSE_WORKSPACE}/checkpoints/${COARSE_RUN_NAME}.pth"
    if [[ ! -s "${INIT_CKPT}" ]]; then
      echo "Missing coarse-stage checkpoint: ${INIT_CKPT}" >&2
      exit 1
    fi
    COMMAND=(
      "${COMMON_ARGS[@]}"
      --dmtet
      --init_ckpt "${INIT_CKPT}"
      --known_view_interval 4
      --lambda_guidance 1e-3 0.01
      --rm_edge
    )
    ;;
  *)
    echo "STAGE must be coarse or fine" >&2
    exit 2
    ;;
esac

cd -- "${MAGIC123_ROOT}"
CUDA_VISIBLE_DEVICES="${GPU}" "${CONDA_BIN}" run -n "${MAGIC123_ENV}" --no-capture-output \
  python "${PROJECT_ROOT}/scripts/run_tracked_experiment.py" \
  --stage "object_c_magic123_${STAGE}" \
  --run-name "${RUN_NAME}" \
  --cwd "${MAGIC123_ROOT}" \
  --output "${WORKSPACE}" \
  --metric-prefix magic123 \
  --config "mode=${MODE}" \
  --config "iterations=${ITERS}" \
  --config "width=${WIDTH}" \
  --config "height=${HEIGHT}" \
  --config "prompt=${TEXT_PROMPT}" \
  --config "sd_model=${MAGIC123_SD_MODEL}" \
  --swanlab-mode "${SWANLAB_MODE:-local}" \
  -- "${COMMAND[@]}"
