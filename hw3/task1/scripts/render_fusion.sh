#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
BLENDER_BIN="${BLENDER_BIN:-${PROJECT_ROOT}/external/blender/blender}"
FUSION_CONFIG="${FUSION_CONFIG:-${PROJECT_ROOT}/configs/fusion_scene.json}"

if [[ ! -x "${BLENDER_BIN}" ]]; then
  echo "Missing Blender runtime. Run: bash scripts/setup_blender.sh" >&2
  exit 1
fi

"${BLENDER_BIN}" \
  --background \
  --python "${PROJECT_ROOT}/scripts/blender_fuse_scene.py" \
  -- \
  --config "${FUSION_CONFIG}"
