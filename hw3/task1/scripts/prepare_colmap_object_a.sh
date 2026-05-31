#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
RAW_IMAGES="${PROJECT_ROOT}/data/raw/object_a_images"
OUTPUT_DIR="${PROJECT_ROOT}/data/processed/object_a_2dgs_ready"
CONVERTER="${PROJECT_ROOT}/external/2d-gaussian-splatting/convert.py"

if [[ "${1:-}" == "--force" ]]; then
  rm -rf -- "${OUTPUT_DIR}"
elif [[ -e "${OUTPUT_DIR}" ]]; then
  echo "Output already exists: ${OUTPUT_DIR}"
  echo "Re-run with --force to rebuild it."
  exit 1
fi

if [[ ! -d "${RAW_IMAGES}" ]]; then
  echo "Missing Object A images: ${RAW_IMAGES}"
  exit 1
fi

if [[ ! -f "${CONVERTER}" ]]; then
  echo "Missing official 2DGS converter: ${CONVERTER}"
  exit 1
fi

mkdir -p -- "${OUTPUT_DIR}/input"
find "${RAW_IMAGES}" -maxdepth 1 -type f \
  \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) \
  -exec cp -- {} "${OUTPUT_DIR}/input/" \;

python "${CONVERTER}" --source_path "${OUTPUT_DIR}"
