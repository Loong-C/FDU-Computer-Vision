#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
BLENDER_VERSION="${BLENDER_VERSION:-4.2.15}"
BLENDER_SERIES="${BLENDER_SERIES:-Blender4.2}"
ARCHIVE="blender-${BLENDER_VERSION}-linux-x64.tar.xz"
CACHE_DIR="${PROJECT_ROOT}/data/raw/tooling/blender"
INSTALL_DIR="${PROJECT_ROOT}/external/blender"
BASE_URL="https://download.blender.org/release/${BLENDER_SERIES}"
WSL_GATEWAY="$(ip route show default | awk '{print $3; exit}')"
export HTTP_PROXY="${HTTP_PROXY:-http://${WSL_GATEWAY}:7890}"
export HTTPS_PROXY="${HTTPS_PROXY:-${HTTP_PROXY}}"

if [[ -x "${INSTALL_DIR}/blender" ]]; then
  "${INSTALL_DIR}/blender" --version | head -n 1
  exit
fi

mkdir -p "${CACHE_DIR}" "${INSTALL_DIR}"
curl --fail --location --retry 5 --retry-delay 2 \
  --continue-at - \
  --output "${CACHE_DIR}/${ARCHIVE}.part" \
  "${BASE_URL}/${ARCHIVE}"
mv -- "${CACHE_DIR}/${ARCHIVE}.part" "${CACHE_DIR}/${ARCHIVE}"

curl --fail --location --retry 5 --retry-delay 2 \
  --output "${CACHE_DIR}/blender-${BLENDER_VERSION}.sha256" \
  "${BASE_URL}/blender-${BLENDER_VERSION}.sha256"

(
  cd -- "${CACHE_DIR}"
  grep " ${ARCHIVE}$" "blender-${BLENDER_VERSION}.sha256" | sha256sum --check -
)

tar --extract --file "${CACHE_DIR}/${ARCHIVE}" \
  --directory "${INSTALL_DIR}" \
  --strip-components 1

"${INSTALL_DIR}/blender" --version | head -n 1
