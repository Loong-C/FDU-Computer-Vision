#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WSL_GATEWAY="$(ip route show default | awk '{print $3; exit}')"
export HTTP_PROXY="${HTTP_PROXY:-http://${WSL_GATEWAY}:7890}"
export HTTPS_PROXY="${HTTPS_PROXY:-${HTTP_PROXY}}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"

python "${SCRIPT_DIR}/download_hf_background_counter.py"
