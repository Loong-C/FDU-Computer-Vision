#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
GH_BIN="${GH_BIN:-/mnt/d/Program Files/GitHub CLI/gh.exe}"
PYTHON_BIN="${PYTHON_BIN:-/home/hp/miniforge3/envs/cv_hw3_threestudio/bin/python}"
RELEASE_DIR="${RELEASE_DIR:-/mnt/d/PackageCache/cv-hw3-task1-release}"
REPO="${REPO:-Loong-C/FDU-Computer-Vision}"
TAG="${TAG:-hw3-task1-weights}"
ASSET_NAME="cv-hw3-task1-best-weights.tar.gz"
WALKTHROUGH_NAME="task1-walkthrough.mp4"
ARCHIVE="${RELEASE_DIR}/${ASSET_NAME}"
CHECKSUM="${ARCHIVE}.sha256"
NOTES="${RELEASE_DIR}/release-notes.md"
WALKTHROUGH="${PROJECT_ROOT}/outputs/fusion/${WALKTHROUGH_NAME}"
CLOUD_WEIGHTS_URL="https://github.com/${REPO}/releases/download/${TAG}/${ASSET_NAME}"
PUBLIC_WALKTHROUGH_URL="https://github.com/${REPO}/releases/download/${TAG}/${WALKTHROUGH_NAME}"

if [[ ! -f "${GH_BIN}" ]]; then
  echo "Missing Windows GitHub CLI: ${GH_BIN}" >&2
  exit 1
fi
if [[ ! -s "${WALKTHROUGH}" ]]; then
  echo "Missing formal walkthrough video: ${WALKTHROUGH}" >&2
  exit 1
fi

"${PYTHON_BIN}" "${SCRIPT_DIR}/package_best_weights.py" --release-dir "${RELEASE_DIR}"
ARCHIVE_WINDOWS="$(wslpath -w "${ARCHIVE}")"
CHECKSUM_WINDOWS="$(wslpath -w "${CHECKSUM}")"
NOTES_WINDOWS="$(wslpath -w "${NOTES}")"
WALKTHROUGH_WINDOWS="$(wslpath -w "${WALKTHROUGH}")"

if "${GH_BIN}" release view "${TAG}" --repo "${REPO}" >/dev/null 2>&1; then
  "${GH_BIN}" release upload "${TAG}" \
    "${ARCHIVE_WINDOWS}" \
    "${CHECKSUM_WINDOWS}" \
    "${WALKTHROUGH_WINDOWS}" \
    --repo "${REPO}" \
    --clobber
else
  "${GH_BIN}" release create "${TAG}" \
    "${ARCHIVE_WINDOWS}" \
    "${CHECKSUM_WINDOWS}" \
    "${WALKTHROUGH_WINDOWS}" \
    --repo "${REPO}" \
    --target hw3 \
    --title "CV HW3 Task 1 best weights" \
    --notes-file "${NOTES_WINDOWS}"
fi

printf '%s\n' "${CLOUD_WEIGHTS_URL}" >"${RELEASE_DIR}/cloud_weights_url.txt"
printf '%s\n' "${PUBLIC_WALKTHROUGH_URL}" >"${RELEASE_DIR}/public_walkthrough_url.txt"
echo "Published best weights: ${CLOUD_WEIGHTS_URL}"
echo "Published walkthrough: ${PUBLIC_WALKTHROUGH_URL}"
