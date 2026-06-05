#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
BLENDER_VERSION="${BLENDER_VERSION:-4.2.15}"
BLENDER_SERIES="${BLENDER_SERIES:-Blender4.2}"
ARCHIVE="blender-${BLENDER_VERSION}-linux-x64.tar.xz"
CACHE_DIR="${BLENDER_CACHE_DIR:-/mnt/d/PackageCache/wsl/blender}"
INSTALL_DIR="${PROJECT_ROOT}/external/blender"
BASE_URL="https://download.blender.org/release/${BLENDER_SERIES}"
WSL_GATEWAY="$(ip route show default | awk '{print $3; exit}')"
export HTTP_PROXY="${HTTP_PROXY:-http://${WSL_GATEWAY}:7890}"
export HTTPS_PROXY="${HTTPS_PROXY:-${HTTP_PROXY}}"

verify_blender() {
  local output
  if ! output="$(
    "${INSTALL_DIR}/blender" \
      --background \
      --python-expr "import encodings; print('Blender runtime OK')" \
      2>&1
  )"; then
    printf '%s\n' "${output}" >&2
    return 1
  fi
  printf '%s\n' "${output}" | grep -m 1 "Blender runtime OK"
}

if [[ -x "${INSTALL_DIR}/blender" ]]; then
  if verify_blender; then
    exit
  fi
  if [[ "$(realpath -m -- "${INSTALL_DIR}")" != "${PROJECT_ROOT}/external/blender" ]]; then
    echo "Refusing to remove unexpected Blender directory: ${INSTALL_DIR}" >&2
    exit 1
  fi
  echo "Existing Blender runtime is incomplete; reinstalling it." >&2
  rm -rf -- "${INSTALL_DIR}"
fi

mkdir -p "${CACHE_DIR}" "${INSTALL_DIR}"
curl --fail --location --retry 5 --retry-delay 2 \
  --output "${CACHE_DIR}/blender-${BLENDER_VERSION}.sha256" \
  "${BASE_URL}/blender-${BLENDER_VERSION}.sha256"

if ! (
  cd -- "${CACHE_DIR}"
  grep " ${ARCHIVE}$" "blender-${BLENDER_VERSION}.sha256" |
    sha256sum --check --status -
); then
  curl --fail --location --retry 5 --retry-delay 2 \
    --continue-at - \
    --output "${CACHE_DIR}/${ARCHIVE}.part" \
    "${BASE_URL}/${ARCHIVE}"
  mv -- "${CACHE_DIR}/${ARCHIVE}.part" "${CACHE_DIR}/${ARCHIVE}"
fi

(
  cd -- "${CACHE_DIR}"
  grep " ${ARCHIVE}$" "blender-${BLENDER_VERSION}.sha256" | sha256sum --check -
)

tar --extract --file "${CACHE_DIR}/${ARCHIVE}" \
  --directory "${INSTALL_DIR}" \
  --strip-components 1

if ! verify_blender; then
  echo "Blender reinstall completed but the runtime still cannot start." >&2
  echo "Install the WSL libraries: bash scripts/install_blender_wsl_deps.sh" >&2
  exit 1
fi
