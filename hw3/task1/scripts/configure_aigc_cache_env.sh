#!/usr/bin/env bash
set -euo pipefail

if [[ -d /mnt/d ]]; then
  export HF_HOME="${HF_HOME:-/mnt/d/PackageCache/wsl/huggingface}"
  mkdir -p -- "${HF_HOME}"
fi

export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HUB_DOWNLOAD_TIMEOUT="${HF_HUB_DOWNLOAD_TIMEOUT:-600}"

if [[ -n "${WINDOWS_PROXY_PORT:-}" ]]; then
  WINDOWS_PROXY_HOST="${WINDOWS_PROXY_HOST:-$(ip route | awk '/default/ {print $3; exit}')}"
  WINDOWS_PROXY_URL="http://${WINDOWS_PROXY_HOST}:${WINDOWS_PROXY_PORT}"
  export HTTP_PROXY="${HTTP_PROXY:-${WINDOWS_PROXY_URL}}"
  export HTTPS_PROXY="${HTTPS_PROXY:-${WINDOWS_PROXY_URL}}"
fi
