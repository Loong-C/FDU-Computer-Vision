#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
BLENDER_BIN="${PROJECT_ROOT}/external/blender/blender"

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=()
elif command -v sudo >/dev/null 2>&1; then
  SUDO=(sudo)
else
  echo "Run this script as root or install sudo first." >&2
  exit 1
fi

"${SUDO[@]}" apt-get update
DEBIAN_FRONTEND=noninteractive "${SUDO[@]}" apt-get install -y libsm6 libice6

if [[ -x "${BLENDER_BIN}" ]]; then
  "${BLENDER_BIN}" --version | head -n 1
else
  echo "Blender dependencies installed. Run: bash scripts/setup_blender.sh"
fi
