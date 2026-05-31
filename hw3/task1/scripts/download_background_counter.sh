#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
RAW_DIR="${PROJECT_ROOT}/data/raw/mipnerf360"
ARCHIVE="${RAW_DIR}/360_v2.zip"
SCENE_DIR="${RAW_DIR}/360_v2/counter"
PROCESSED_LINK="${PROJECT_ROOT}/data/processed/background_counter"
URL="https://storage.googleapis.com/gresearch/refraw360/360_v2.zip"

mkdir -p -- "${RAW_DIR}" "${PROJECT_ROOT}/data/processed"

if [[ ! -f "${ARCHIVE}" ]]; then
  touch -- "${ARCHIVE}"
fi

echo "Downloading with resume support: ${URL}"
curl --fail --location --continue-at - --output "${ARCHIVE}" "${URL}"

if [[ ! -d "${SCENE_DIR}" ]]; then
  echo "Extracting counter scene..."
  unzip -q "${ARCHIVE}" '360_v2/counter/*' -d "${RAW_DIR}"
fi

ln -sfn -- "${SCENE_DIR}" "${PROCESSED_LINK}"
echo "Background scene ready: ${PROCESSED_LINK}"
