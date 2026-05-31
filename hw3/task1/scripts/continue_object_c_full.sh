#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
COARSE_RUN_NAME="${COARSE_RUN_NAME:-object-c-magic123-coarse-full}"
FINE_RUN_NAME="${FINE_RUN_NAME:-object-c-magic123-fine-full}"

export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"

verify_wrapper_success() {
  local metadata_path="$1"
  /home/hp/miniforge3/bin/python - "${metadata_path}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit(f"Missing wrapper metadata: {path}")
metadata = json.loads(path.read_text(encoding="utf-8"))
exit_code = metadata.get("exit_code")
if exit_code != 0:
    raise SystemExit(f"Wrapper failed with exit code {exit_code}: {path}")
print(f"Verified wrapper success: {path}")
PY
}

verify_nonempty_file() {
  local path="$1"
  if [[ ! -s "${path}" ]]; then
    echo "Missing required output: ${path}" >&2
    exit 1
  fi
  echo "Verified output: ${path}"
}

COARSE_METADATA="${PROJECT_ROOT}/logs/${COARSE_RUN_NAME}.json"
COARSE_CHECKPOINT="${PROJECT_ROOT}/outputs/object_c_magic123/${COARSE_RUN_NAME}/checkpoints/${COARSE_RUN_NAME}.pth"
FINE_METADATA="${PROJECT_ROOT}/logs/${FINE_RUN_NAME}.json"
FINE_MESH="${PROJECT_ROOT}/outputs/object_c_magic123/${FINE_RUN_NAME}/mesh/mesh.obj"

if [[ -s "${COARSE_METADATA}" ]]; then
  echo "Reusing completed Object C coarse full run."
else
  echo "Running Object C Magic123 coarse full stage."
  MODE=full \
    STAGE=coarse \
    RUN_NAME="${COARSE_RUN_NAME}" \
    bash "${SCRIPT_DIR}/generate_image3d_object_c.sh" \
    >"${PROJECT_ROOT}/logs/${COARSE_RUN_NAME}-launch.log" 2>&1
fi
verify_wrapper_success "${COARSE_METADATA}"
verify_nonempty_file "${COARSE_CHECKPOINT}"

if [[ -s "${FINE_METADATA}" ]]; then
  echo "Reusing completed Object C fine full run."
else
  echo "Running Object C Magic123 fine full stage."
  MODE=full \
    STAGE=fine \
    RUN_NAME="${FINE_RUN_NAME}" \
    COARSE_RUN_NAME="${COARSE_RUN_NAME}" \
    bash "${SCRIPT_DIR}/generate_image3d_object_c.sh" \
    >"${PROJECT_ROOT}/logs/${FINE_RUN_NAME}-launch.log" 2>&1
fi
verify_wrapper_success "${FINE_METADATA}"
verify_nonempty_file "${FINE_MESH}"

echo "Object C full coarse and fine queue completed successfully."
