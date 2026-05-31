#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
MAGIC123_ROOT="${PROJECT_ROOT}/external/Magic123"
WSL_GATEWAY="$(ip route show default | awk '{print $3; exit}')"
export HTTP_PROXY="${HTTP_PROXY:-http://${WSL_GATEWAY}:7890}"
export HTTPS_PROXY="${HTTPS_PROXY:-${HTTP_PROXY}}"

download_file() {
  local url="$1"
  local destination="$2"
  local partial="${destination}.part"
  if [[ -s "${destination}" ]]; then
    echo "Already downloaded: ${destination}"
    return
  fi
  mkdir -p "$(dirname -- "${destination}")"
  curl --fail --location --retry 5 --retry-delay 2 \
    --continue-at - \
    --output "${partial}" \
    "${url}"
  mv -- "${partial}" "${destination}"
}

download_file \
  "https://huggingface.co/cvlab/zero123-weights/resolve/main/105000.ckpt" \
  "${MAGIC123_ROOT}/pretrained/zero123/105000.ckpt"

download_file \
  "https://github.com/isl-org/MiDaS/releases/download/v3_1/dpt_beit_large_512.pt" \
  "${MAGIC123_ROOT}/pretrained/midas/dpt_beit_large_512.pt"
