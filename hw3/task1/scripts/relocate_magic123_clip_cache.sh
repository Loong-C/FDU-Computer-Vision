#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d /mnt/d ]]; then
  exit 0
fi

CACHE_LINK="${HOME}/.cache/clip"
CACHE_TARGET="${MAGIC123_CLIP_CACHE_DIR:-/mnt/d/PackageCache/wsl/clip}"

mkdir -p -- "$(dirname -- "${CACHE_LINK}")" "${CACHE_TARGET}"

if [[ -L "${CACHE_LINK}" ]]; then
  if [[ "$(readlink -f -- "${CACHE_LINK}")" != "$(readlink -f -- "${CACHE_TARGET}")" ]]; then
    echo "Existing CLIP cache symlink points outside the managed D-drive cache: ${CACHE_LINK}" >&2
    exit 1
  fi
  echo "Magic123 CLIP cache already points to ${CACHE_TARGET}."
  exit 0
fi

if [[ -e "${CACHE_LINK}" && ! -d "${CACHE_LINK}" ]]; then
  echo "Expected a directory or symlink at ${CACHE_LINK}" >&2
  exit 1
fi

if [[ -d "${CACHE_LINK}" ]]; then
  shopt -s dotglob nullglob
  for source_path in "${CACHE_LINK}"/*; do
    target_path="${CACHE_TARGET}/$(basename -- "${source_path}")"
    if [[ -e "${target_path}" ]]; then
      if [[ -f "${source_path}" && -f "${target_path}" ]] && cmp -s -- "${source_path}" "${target_path}"; then
        rm -- "${source_path}"
      else
        echo "Refusing to overwrite an existing CLIP cache entry: ${target_path}" >&2
        exit 1
      fi
    else
      mv -- "${source_path}" "${CACHE_TARGET}/"
    fi
  done
  rmdir -- "${CACHE_LINK}"
fi

ln -s -- "${CACHE_TARGET}" "${CACHE_LINK}"
echo "Magic123 CLIP cache linked to ${CACHE_TARGET}."
