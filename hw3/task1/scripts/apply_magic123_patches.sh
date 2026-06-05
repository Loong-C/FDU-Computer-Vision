#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
MAGIC123_ROOT="${PROJECT_ROOT}/external/Magic123"
PATCH_FILE="${PROJECT_ROOT}/patches/magic123-disable-unused-safety-checker.patch"

if [[ ! -d "${MAGIC123_ROOT}/.git" ]]; then
  echo "Magic123 repository not found: ${MAGIC123_ROOT}" >&2
  exit 1
fi

if git -C "${MAGIC123_ROOT}" apply --check "${PATCH_FILE}" >/dev/null 2>&1; then
  git -C "${MAGIC123_ROOT}" apply "${PATCH_FILE}"
  echo "Applied Magic123 pipeline compatibility patch."
elif git -C "${MAGIC123_ROOT}" apply --reverse --check "${PATCH_FILE}" >/dev/null 2>&1; then
  echo "Magic123 pipeline compatibility patch already applied."
else
  echo "Magic123 compatibility patch does not apply cleanly." >&2
  echo "Inspect ${MAGIC123_ROOT}/guidance/sd_utils.py before continuing." >&2
  exit 1
fi
