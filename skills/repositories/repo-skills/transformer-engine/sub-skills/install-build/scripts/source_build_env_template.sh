#!/usr/bin/env bash
# Transformer Engine source-build environment template.
#
# Usage:
#   bash source_build_env_template.sh --help
#   bash source_build_env_template.sh --print
#   bash source_build_env_template.sh --install
#
# Default behavior is non-destructive: without --install this script prints
# usage and exits before running pip. Run it from the Transformer Engine source
# checkout you intend to build. Edit or override the variables below for the
# target machine; do not hard-code private environment prefixes into a shared
# copy of this template.

set -euo pipefail

usage() {
  cat <<'USAGE'
Transformer Engine source-build template

This template exports build variables and, only with --install, runs:
  python -m pip install --no-build-isolation -e .

Common invocations:
  # Inspect the command that would run.
  bash source_build_env_template.sh --print

  # A100/SM80 both-framework editable build; NCCL EP disabled.
  NVTE_FRAMEWORK=all NVTE_CUDA_ARCHS=80 NVTE_WITH_NCCL_EP=0 \
    bash source_build_env_template.sh --install

  # PyTorch-only or JAX-only builds.
  NVTE_FRAMEWORK=pytorch bash source_build_env_template.sh --install
  NVTE_FRAMEWORK=jax bash source_build_env_template.sh --install

Important placeholders to set when not using default system locations:
  CUDA_HOME=/path/to/cuda-toolkit
  CUDNN_HOME=/path/to/cudnn
  NCCL_HOME=/path/to/nccl

No broad dev/test extras are installed by this script.
USAGE
}

mode="${1:---help}"
case "$mode" in
  --help|-h)
    usage
    exit 0
    ;;
  --print|--install)
    ;;
  *)
    echo "Unknown argument: $mode" >&2
    usage >&2
    exit 2
    ;;
esac

# User-overridable build selection. The defaults are conservative for the
# verified A100/SM80 profile. Override for Hopper/Blackwell or framework-specific
# builds as needed.
: "${NVTE_FRAMEWORK:=all}"
: "${NVTE_CUDA_ARCHS:=80}"
: "${NVTE_WITH_NCCL_EP:=0}"
: "${NVTE_BUILD_MAX_JOBS:=4}"
: "${MAX_JOBS:=${NVTE_BUILD_MAX_JOBS}}"
: "${NVTE_BUILD_THREADS_PER_JOB:=1}"

# Optional toolkit/library placeholders. Leave empty when the active environment
# already exposes the intended toolkit and libraries.
: "${CUDA_HOME:=}"
: "${CUDNN_HOME:=}"
: "${NCCL_HOME:=}"

export NVTE_FRAMEWORK NVTE_CUDA_ARCHS NVTE_WITH_NCCL_EP
export NVTE_BUILD_MAX_JOBS MAX_JOBS NVTE_BUILD_THREADS_PER_JOB

if [[ -n "$CUDA_HOME" ]]; then
  export CUDA_HOME
  export CUDA_PATH="${CUDA_PATH:-$CUDA_HOME}"
  export PATH="$CUDA_HOME/bin:$PATH"
  export LD_LIBRARY_PATH="$CUDA_HOME/lib64:$CUDA_HOME/lib:${LD_LIBRARY_PATH:-}"
fi

if [[ -n "$CUDNN_HOME" ]]; then
  export CUDNN_HOME
  export CUDNN_PATH="${CUDNN_PATH:-$CUDNN_HOME}"
  export LD_LIBRARY_PATH="$CUDNN_HOME/lib:$CUDNN_HOME/lib64:${LD_LIBRARY_PATH:-}"
fi

if [[ -n "$NCCL_HOME" ]]; then
  export NCCL_HOME
  export LD_LIBRARY_PATH="$NCCL_HOME/lib:$NCCL_HOME/lib64:${LD_LIBRARY_PATH:-}"
fi

cat <<CONFIG
Transformer Engine source-build environment:
  NVTE_FRAMEWORK=$NVTE_FRAMEWORK
  NVTE_CUDA_ARCHS=$NVTE_CUDA_ARCHS
  NVTE_WITH_NCCL_EP=$NVTE_WITH_NCCL_EP
  NVTE_BUILD_MAX_JOBS=$NVTE_BUILD_MAX_JOBS
  MAX_JOBS=$MAX_JOBS
  NVTE_BUILD_THREADS_PER_JOB=$NVTE_BUILD_THREADS_PER_JOB
  CUDA_HOME=${CUDA_HOME:-<unset>}
  CUDNN_HOME=${CUDNN_HOME:-<unset>}
  NCCL_HOME=${NCCL_HOME:-<unset>}
CONFIG

if [[ "$mode" == "--print" ]]; then
  cat <<'COMMAND'
Command not executed. To build explicitly, run with --install.
Would run:
  python -m pip install --no-build-isolation -e .
COMMAND
  exit 0
fi

python - <<'PY'
import os, shutil, sys
print('python', sys.version.split()[0])
print('nvcc', shutil.which('nvcc') or '<not-found>')
for key in ['NVTE_FRAMEWORK', 'NVTE_CUDA_ARCHS', 'NVTE_WITH_NCCL_EP',
            'NVTE_BUILD_MAX_JOBS', 'MAX_JOBS', 'CUDA_HOME', 'CUDNN_HOME', 'NCCL_HOME']:
    print(f'{key}={os.environ.get(key, "<unset>")}')
PY

python -m pip install --no-build-isolation -e .
