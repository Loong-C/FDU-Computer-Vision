#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd -- "${PROJECT_ROOT}/../.." && pwd)"
CONDA_BIN="${CONDA_BIN:-/home/hp/miniforge3/bin/conda}"
WAIT_SECONDS="${WAIT_SECONDS:-60}"
FINE_RUN_NAME="${FINE_RUN_NAME:-object-c-magic123-fine-full}"
FORMAL_RUN_NAME="${FORMAL_RUN_NAME:-task1-fusion-render}"
LOG_PATH="${PROJECT_ROOT}/logs/continue-after-object-c-full.log"

mkdir -p "${PROJECT_ROOT}/logs"
exec >>"${LOG_PATH}" 2>&1

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

wait_for_file() {
  local path="$1"
  while [[ ! -s "${path}" ]]; do
    echo "Waiting for ${path} ($(date --iso-8601=seconds))"
    sleep "${WAIT_SECONDS}"
  done
}

echo "Starting post-Object-C formalization queue at $(date --iso-8601=seconds)"
FINE_METADATA="${PROJECT_ROOT}/logs/${FINE_RUN_NAME}.json"
FINE_MESH="${PROJECT_ROOT}/outputs/object_c_magic123/${FINE_RUN_NAME}/mesh/mesh.obj"
wait_for_file "${FINE_METADATA}"
verify_wrapper_success "${FINE_METADATA}"
verify_nonempty_file "${FINE_MESH}"

FINE_PREVIEW="$(
  find "${PROJECT_ROOT}/outputs/object_c_magic123/${FINE_RUN_NAME}/results" \
    -type f -name "*lambertian.jpg" -print |
    sort |
    tail -n 1
)"
verify_nonempty_file "${FINE_PREVIEW}"
cp -f -- "${FINE_PREVIEW}" "${PROJECT_ROOT}/docs/figures/object_c_magic123_final_preview.jpg"

FORMAL_METADATA="${PROJECT_ROOT}/logs/${FORMAL_RUN_NAME}.json"
FORMAL_VIDEO="${PROJECT_ROOT}/outputs/fusion/task1-walkthrough.mp4"
FORMAL_PREVIEW="${PROJECT_ROOT}/outputs/fusion/task1-walkthrough-preview.png"
if [[ -s "${FORMAL_METADATA}" && -s "${FORMAL_VIDEO}" && -s "${FORMAL_PREVIEW}" ]]; then
  echo "Reusing completed formal fusion render."
else
  MODE=formal RUN_NAME="${FORMAL_RUN_NAME}" bash "${SCRIPT_DIR}/render_fusion_tracked.sh"
fi
verify_wrapper_success "${FORMAL_METADATA}"
verify_nonempty_file "${FORMAL_VIDEO}"
verify_nonempty_file "${FORMAL_PREVIEW}"
cp -f -- "${FORMAL_PREVIEW}" "${PROJECT_ROOT}/docs/figures/fusion_walkthrough_preview.png"

"${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
  python "${PROJECT_ROOT}/report/build_report_assets.py"
"${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
  python "${PROJECT_ROOT}/report/generate_report.py"
"${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
  python "${PROJECT_ROOT}/scripts/check_task1_readiness.py" \
  --strict \
  --output "${PROJECT_ROOT}/logs/task1-readiness-after-fusion.json"
"${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
  python "${PROJECT_ROOT}/scripts/log_swanlab_event.py" \
  --run-name task1-post-object-c-formalization-complete \
  --event post_object_c_formalization_complete \
  --config readiness=13/13

/home/hp/miniforge3/bin/python - "${PROJECT_ROOT}/notes/experiment_log.md" "${FORMAL_VIDEO}" <<'PY'
import datetime
import sys
from pathlib import Path

log_path = Path(sys.argv[1])
video_path = Path(sys.argv[2])
marker = "## 2026-05-31 / Object C Formal Mesh and Fusion Auto-Finalization"
text = log_path.read_text(encoding="utf-8")
if marker not in text:
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n{marker}\n\n"
            f"Completed at `{timestamp}`.\n\n"
            "The unattended queue verified the formal Object C fine-stage OBJ, "
            "rendered the Blender walkthrough from the real counter COLMAP camera "
            "path, refreshed report assets and the draft PDF, and passed the strict "
            "Task 1 readiness audit (`13/13`).\n\n"
            f"Formal walkthrough: `{video_path}` ({video_path.stat().st_size} bytes).\n"
        )
PY

cd -- "${REPO_ROOT}"
git add -- \
  hw3/task1/docs/figures/fusion_walkthrough_preview.png \
  hw3/task1/notes/experiment_log.md
git add -f -- hw3/task1/docs/figures/object_c_magic123_final_preview.jpg
git add -u -- hw3/task1/report/assets
if ! git diff --cached --quiet; then
  git commit -m "Record Object C and formal fusion outputs"
  git push origin hw3
fi

echo "Post-Object-C formalization queue completed successfully at $(date --iso-8601=seconds)"
