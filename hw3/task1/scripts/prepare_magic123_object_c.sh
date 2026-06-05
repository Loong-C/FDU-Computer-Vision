#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
MAGIC123_ROOT="${PROJECT_ROOT}/external/Magic123"
SOURCE_RGBA="${PROJECT_ROOT}/data/processed/object_c_image/c_rgba.png"
TARGET_DIR="${MAGIC123_ROOT}/data/hw3/medicine_box"
CONDA_BIN="${CONDA_BIN:-${HOME}/miniforge3/bin/conda}"
MAGIC123_ENV="${MAGIC123_ENV:-cv_hw3_magic123}"

if [[ ! -s "${SOURCE_RGBA}" ]]; then
  echo "Missing prepared Object C input: ${SOURCE_RGBA}" >&2
  exit 1
fi

mkdir -p "${TARGET_DIR}"
cp -- "${SOURCE_RGBA}" "${TARGET_DIR}/main.png"
cp -- "${SOURCE_RGBA}" "${TARGET_DIR}/rgba.png"

if [[ "${COPY_ONLY:-0}" == "1" ]]; then
  echo "Copied Object C RGBA input to ${TARGET_DIR}"
  exit
fi

cd -- "${MAGIC123_ROOT}"
"${CONDA_BIN}" run -n "${MAGIC123_ENV}" --no-capture-output \
  python preprocess_image.py --path "${TARGET_DIR}/main.png"
