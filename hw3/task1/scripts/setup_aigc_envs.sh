#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
CONDA_BIN="${CONDA_BIN:-${HOME}/miniforge3/bin/conda}"
THREESTUDIO_ENV="${THREESTUDIO_ENV:-cv_hw3_threestudio}"
MAGIC123_ENV="${MAGIC123_ENV:-cv_hw3_magic123}"
CUDA_CHANNEL="${CUDA_CHANNEL:-nvidia/label/cuda-11.8.0}"

WSL_GATEWAY="$(ip route show default | awk '{print $3; exit}')"
export HTTP_PROXY="${HTTP_PROXY:-http://${WSL_GATEWAY}:7890}"
export HTTPS_PROXY="${HTTPS_PROXY:-${HTTP_PROXY}}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"
if [[ -d /mnt/d ]]; then
  WSL_PIP_CACHE_DIR="${WSL_PIP_CACHE_DIR:-/mnt/d/PackageCache/wsl/pip}"
  mkdir -p "${WSL_PIP_CACHE_DIR}"
  export PIP_CACHE_DIR="${PIP_CACHE_DIR:-${WSL_PIP_CACHE_DIR}}"
fi

env_exists() {
  "${CONDA_BIN}" env list | awk '{print $1}' | grep -Fxq "$1"
}

create_env() {
  local env_name="$1"
  if env_exists "${env_name}"; then
    echo "Conda environment already exists: ${env_name}"
    return
  fi
  "${CONDA_BIN}" create -y -n "${env_name}" python=3.10 pip
}

install_toolchain() {
  local env_name="$1"
  "${CONDA_BIN}" install -y -n "${env_name}" \
    -c "${CUDA_CHANNEL}" \
    -c conda-forge \
    cuda-nvcc=11.8 \
    cuda-cudart-dev=11.8 \
    cuda-libraries-dev=11.8 \
    gcc_linux-64=11 \
    gxx_linux-64=11 \
    ninja
}

install_torch() {
  local env_name="$1"
  "${CONDA_BIN}" run -n "${env_name}" python -m pip install \
    torch==2.0.1 \
    torchvision==0.15.2 \
    "numpy<2" \
    --index-url https://download.pytorch.org/whl/cu118
}

install_tracking() {
  local env_name="$1"
  "${CONDA_BIN}" run -n "${env_name}" python -m pip install \
    "swanlab[dashboard]" \
    tensorboard \
    pyyaml
}

install_build_prereqs() {
  local env_name="$1"
  "${CONDA_BIN}" run -n "${env_name}" python -m pip install \
    "setuptools<81" \
    wheel \
    packaging
}

install_threestudio_deps() {
  local env_prefix="${HOME}/miniforge3/envs/${THREESTUDIO_ENV}"
  install_build_prereqs "${THREESTUDIO_ENV}"
  "${CONDA_BIN}" run -n "${THREESTUDIO_ENV}" env \
    CUDA_HOME="${env_prefix}" \
    CC="${env_prefix}/bin/x86_64-conda-linux-gnu-cc" \
    CXX="${env_prefix}/bin/x86_64-conda-linux-gnu-c++" \
    python -m pip install --no-build-isolation \
    -c "${PROJECT_ROOT}/requirements-threestudio-compatibility.txt" \
    -r "${PROJECT_ROOT}/external/threestudio/requirements.txt"
}

install_magic123_deps() {
  local env_prefix="${HOME}/miniforge3/envs/${MAGIC123_ENV}"
  install_build_prereqs "${MAGIC123_ENV}"
  "${CONDA_BIN}" run -n "${MAGIC123_ENV}" env \
    CUDA_HOME="${env_prefix}" \
    CC="${env_prefix}/bin/x86_64-conda-linux-gnu-cc" \
    CXX="${env_prefix}/bin/x86_64-conda-linux-gnu-c++" \
    python -m pip install --no-build-isolation \
    -c "${PROJECT_ROOT}/requirements-magic123-compatibility.txt" \
    -r "${PROJECT_ROOT}/external/Magic123/requirements.txt"
  "${CONDA_BIN}" run -n "${MAGIC123_ENV}" python -m pip install \
    -r "${PROJECT_ROOT}/requirements-magic123-compatibility.txt"
  (
    cd -- "${PROJECT_ROOT}/external/Magic123"
    "${CONDA_BIN}" run -n "${MAGIC123_ENV}" env \
      CUDA_HOME="${env_prefix}" \
      CC="${env_prefix}/bin/x86_64-conda-linux-gnu-cc" \
      CXX="${env_prefix}/bin/x86_64-conda-linux-gnu-c++" \
      MAX_JOBS="${MAX_JOBS:-2}" \
      python -m pip install --no-build-isolation \
      ./raymarching \
      ./shencoder \
      ./freqencoder \
      ./gridencoder
  )
}

case "${1:-bootstrap}" in
  bootstrap)
    create_env "${THREESTUDIO_ENV}"
    create_env "${MAGIC123_ENV}"
    ;;
  toolchain)
    install_toolchain "${THREESTUDIO_ENV}"
    install_toolchain "${MAGIC123_ENV}"
    ;;
  torch)
    install_torch "${THREESTUDIO_ENV}"
    install_torch "${MAGIC123_ENV}"
    ;;
  tracking)
    install_tracking "${THREESTUDIO_ENV}"
    install_tracking "${MAGIC123_ENV}"
    ;;
  threestudio-deps)
    install_threestudio_deps
    ;;
  magic123-deps)
    install_magic123_deps
    ;;
  *)
    echo "Usage: $0 {bootstrap|toolchain|torch|tracking|threestudio-deps|magic123-deps}" >&2
    exit 2
    ;;
esac
