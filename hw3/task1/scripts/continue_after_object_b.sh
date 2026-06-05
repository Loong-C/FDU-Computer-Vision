#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
OBJECT_B_RUN_NAME="${OBJECT_B_RUN_NAME:-object-b-dreamfusion-sd-full}"
OBJECT_C_COARSE_RUN_NAME="${OBJECT_C_COARSE_RUN_NAME:-object-c-magic123-coarse-smoke}"
OBJECT_C_FINE_RUN_NAME="${OBJECT_C_FINE_RUN_NAME:-object-c-magic123-fine-smoke}"
POLL_SECONDS="${POLL_SECONDS:-60}"

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

echo "Waiting for Object B formal wrapper: ${OBJECT_B_RUN_NAME}"
while pgrep -f "run_tracked_experiment.py --stage object_b_text3d --run-name ${OBJECT_B_RUN_NAME}" >/dev/null; do
  sleep "${POLL_SECONDS}"
done

verify_wrapper_success "${PROJECT_ROOT}/logs/${OBJECT_B_RUN_NAME}.json"

echo "Exporting Object B formal OBJ."
RUN_NAME="${OBJECT_B_RUN_NAME}" \
  bash "${SCRIPT_DIR}/export_text3d_object_b.sh" \
  >"${PROJECT_ROOT}/logs/${OBJECT_B_RUN_NAME}-export-launch.log" 2>&1
verify_wrapper_success "${PROJECT_ROOT}/logs/${OBJECT_B_RUN_NAME}-export.json"

echo "Running Object C Magic123 coarse smoke."
MODE=smoke \
  STAGE=coarse \
  RUN_NAME="${OBJECT_C_COARSE_RUN_NAME}" \
  bash "${SCRIPT_DIR}/generate_image3d_object_c.sh" \
  >"${PROJECT_ROOT}/logs/${OBJECT_C_COARSE_RUN_NAME}-launch.log" 2>&1
verify_wrapper_success "${PROJECT_ROOT}/logs/${OBJECT_C_COARSE_RUN_NAME}.json"

echo "Running Object C Magic123 fine smoke."
MODE=smoke \
  STAGE=fine \
  RUN_NAME="${OBJECT_C_FINE_RUN_NAME}" \
  COARSE_RUN_NAME="${OBJECT_C_COARSE_RUN_NAME}" \
  bash "${SCRIPT_DIR}/generate_image3d_object_c.sh" \
  >"${PROJECT_ROOT}/logs/${OBJECT_C_FINE_RUN_NAME}-launch.log" 2>&1
verify_wrapper_success "${PROJECT_ROOT}/logs/${OBJECT_C_FINE_RUN_NAME}.json"

echo "Object B export and Object C smoke queue completed successfully."
