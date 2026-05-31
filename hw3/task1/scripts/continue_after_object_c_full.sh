#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd -- "${PROJECT_ROOT}/../.." && pwd)"
CONDA_BIN="${CONDA_BIN:-/home/hp/miniforge3/bin/conda}"
PYTHON_BIN="${PYTHON_BIN:-/home/hp/miniforge3/envs/cv_hw3_threestudio/bin/python}"
WAIT_SECONDS="${WAIT_SECONDS:-60}"
READINESS_ATTEMPTS="${READINESS_ATTEMPTS:-3}"
READINESS_RETRY_SECONDS="${READINESS_RETRY_SECONDS:-15}"
FINE_RUN_NAME="${FINE_RUN_NAME:-object-c-magic123-fine-full}"
FORMAL_RUN_NAME="${FORMAL_RUN_NAME:-task1-fusion-render}"
RELEASE_RUN_NAME="${RELEASE_RUN_NAME:-task1-best-weights-release}"
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

wrapper_succeeded() {
  local metadata_path="$1"
  /home/hp/miniforge3/bin/python - "${metadata_path}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    metadata = json.loads(path.read_text(encoding="utf-8"))
except (FileNotFoundError, json.JSONDecodeError, OSError):
    raise SystemExit(1)
raise SystemExit(metadata.get("exit_code") != 0)
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

wait_for_successful_wrapper() {
  local path="$1"
  while ! wrapper_succeeded "${path}"; do
    echo "Waiting for successful wrapper metadata: ${path} ($(date --iso-8601=seconds))"
    sleep "${WAIT_SECONDS}"
  done
}

public_url_succeeded() {
  local url="$1"
  "${PYTHON_BIN}" - "${PROJECT_ROOT}" "${url}" <<'PY'
import json
import sys

sys.path.insert(0, sys.argv[1])
from scripts.check_task1_readiness import url_check

result = url_check("cloud_weights_public_url", sys.argv[2])
print(json.dumps(result, indent=2))
raise SystemExit(not result["ready"])
PY
}

verify_strict_readiness() {
  local attempt
  for ((attempt = 1; attempt <= READINESS_ATTEMPTS; attempt += 1)); do
    echo "Running strict Task 1 readiness audit (${attempt}/${READINESS_ATTEMPTS})."
    if "${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
      python "${PROJECT_ROOT}/scripts/check_task1_readiness.py" \
      --strict \
      --output "${PROJECT_ROOT}/logs/task1-readiness-final.json"; then
      return 0
    fi
    if (( attempt < READINESS_ATTEMPTS )); then
      echo "Strict readiness audit failed; retrying in ${READINESS_RETRY_SECONDS}s."
      sleep "${READINESS_RETRY_SECONDS}"
    fi
  done
  echo "Strict Task 1 readiness audit failed after ${READINESS_ATTEMPTS} attempts." >&2
  return 1
}

echo "Starting post-Object-C formalization queue at $(date --iso-8601=seconds)"
FINE_METADATA="${PROJECT_ROOT}/logs/${FINE_RUN_NAME}.json"
FINE_MESH="${PROJECT_ROOT}/outputs/object_c_magic123/${FINE_RUN_NAME}/mesh/mesh.obj"
wait_for_successful_wrapper "${FINE_METADATA}"
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
if wrapper_succeeded "${FORMAL_METADATA}" && [[ -s "${FORMAL_VIDEO}" && -s "${FORMAL_PREVIEW}" ]]; then
  echo "Reusing completed formal fusion render."
else
  MODE=formal RUN_NAME="${FORMAL_RUN_NAME}" bash "${SCRIPT_DIR}/render_fusion_tracked.sh"
fi
verify_wrapper_success "${FORMAL_METADATA}"
verify_nonempty_file "${FORMAL_VIDEO}"
verify_nonempty_file "${FORMAL_PREVIEW}"
cp -f -- "${FORMAL_PREVIEW}" "${PROJECT_ROOT}/docs/figures/fusion_walkthrough_preview.png"

RELEASE_METADATA="${PROJECT_ROOT}/logs/${RELEASE_RUN_NAME}.json"
CLOUD_WEIGHTS_URL_PATH="/mnt/d/PackageCache/cv-hw3-task1-release/cloud_weights_url.txt"
CLOUD_WEIGHTS_URL=""
if wrapper_succeeded "${RELEASE_METADATA}" && [[ -s "${CLOUD_WEIGHTS_URL_PATH}" ]]; then
  CLOUD_WEIGHTS_URL="$(cat -- "${CLOUD_WEIGHTS_URL_PATH}")"
fi
if [[ -n "${CLOUD_WEIGHTS_URL}" ]] && public_url_succeeded "${CLOUD_WEIGHTS_URL}"; then
  echo "Reusing completed public best-weights release."
else
  "${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
    python "${PROJECT_ROOT}/scripts/run_tracked_experiment.py" \
    --stage best_weights_release \
    --run-name "${RELEASE_RUN_NAME}" \
    --cwd "${PROJECT_ROOT}" \
    --output /mnt/d/PackageCache/cv-hw3-task1-release \
    --metric-prefix release \
    --config provider=github_release \
    --config tag=hw3-task1-weights \
    --swanlab-mode local \
    -- \
    bash scripts/publish_best_weights_release.sh
fi
verify_wrapper_success "${RELEASE_METADATA}"
verify_nonempty_file "${CLOUD_WEIGHTS_URL_PATH}"
CLOUD_WEIGHTS_URL="$(cat -- "${CLOUD_WEIGHTS_URL_PATH}")"

"${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
  python "${PROJECT_ROOT}/scripts/finalize_task1_metadata.py" \
  --cloud-weights-url "${CLOUD_WEIGHTS_URL}"
"${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
  python "${PROJECT_ROOT}/report/build_report_assets.py"
"${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
  python "${PROJECT_ROOT}/report/generate_report.py" \
  --final \
  --publish
"${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
  python "${PROJECT_ROOT}/report/render_report.py" \
  report/cv_hw3_task1_report.pdf
verify_strict_readiness
"${CONDA_BIN}" run -n cv_hw3_threestudio --no-capture-output \
  python "${PROJECT_ROOT}/scripts/log_swanlab_event.py" \
  --run-name task1-post-object-c-formalization-complete \
  --event post_object_c_formalization_complete \
  --config readiness=17/17 \
  --config cloud_weights_url="${CLOUD_WEIGHTS_URL}"

/home/hp/miniforge3/bin/python - "${PROJECT_ROOT}/notes/experiment_log.md" "${FORMAL_VIDEO}" <<'PY'
import datetime
import sys
from pathlib import Path

log_path = Path(sys.argv[1])
video_path = Path(sys.argv[2])
marker = "Object C Formal Mesh and Fusion Auto-Finalization"
text = log_path.read_text(encoding="utf-8")
if marker not in text:
    now = datetime.datetime.now().astimezone()
    timestamp = now.isoformat()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## {now.date().isoformat()} / {marker}\n\n"
            f"Completed at `{timestamp}`.\n\n"
            "The unattended queue verified the formal Object C fine-stage OBJ, "
            "rendered the Blender walkthrough from the real counter COLMAP camera "
            "path, uploaded the public best-weights package, refreshed report assets "
            "and the final PDF, and passed the strict Task 1 readiness audit (`17/17`).\n\n"
            f"Formal walkthrough: `{video_path}` ({video_path.stat().st_size} bytes).\n"
        )
PY

cd -- "${REPO_ROOT}"
git add -- \
  hw3/task1/docs/figures/fusion_walkthrough_preview.png \
  hw3/task1/notes/experiment_log.md \
  hw3/task1/notes/report_outline.md \
  hw3/task1/notes/time_cost.md \
  hw3/task1/report/cv_hw3_task1_report.pdf \
  hw3/task1/report/report_data.json
git add -f -- hw3/task1/docs/figures/object_c_magic123_final_preview.jpg
git add -u -- hw3/task1/report/assets
if ! git diff --cached --quiet; then
  git commit -m "Record Object C and formal fusion outputs"
  git push origin hw3
fi

echo "Post-Object-C formalization queue completed successfully at $(date --iso-8601=seconds)"
