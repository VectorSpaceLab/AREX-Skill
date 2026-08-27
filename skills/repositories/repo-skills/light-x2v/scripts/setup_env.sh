#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: source setup_env.sh --lightx2v-path PATH --model-path PATH [--dtype BF16|FP16] [--sensitive-dtype FP32|None] [--profiling-level 0|1|2]

Exports the runtime environment variables used by LightX2V in the current shell.
EOF
}

_return_code() {
  local code="$1"
  if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    return "$code"
  fi
  exit "$code"
}

lightx2v_path=""
model_path=""
dtype="BF16"
sensitive_dtype="None"
profiling_level="2"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --lightx2v-path)
      lightx2v_path="$2"
      shift 2
      ;;
    --model-path)
      model_path="$2"
      shift 2
      ;;
    --dtype)
      dtype="$2"
      shift 2
      ;;
    --sensitive-dtype)
      sensitive_dtype="$2"
      shift 2
      ;;
    --profiling-level)
      profiling_level="$2"
      shift 2
      ;;
    -h|--help)
      usage
      _return_code 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      _return_code 2
      ;;
  esac
done

if [[ -z "$lightx2v_path" || -z "$model_path" ]]; then
  usage
  _return_code 2
fi

export lightx2v_path
export model_path
export PYTHONPATH="${lightx2v_path}:${PYTHONPATH:-}"
export MOONCAKE_CONFIG_PATH="${lightx2v_path}/configs/mooncake_config.json"
export TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTORCH_ALLOC_CONF=expandable_segments:True
export DTYPE="$dtype"
export SENSITIVE_LAYER_DTYPE="$sensitive_dtype"
export PROFILING_DEBUG_LEVEL="$profiling_level"

cat <<EOF
==============================================================================
LightX2V Runtime Environment
------------------------------------------------------------------------------
lightx2v_path: ${lightx2v_path}
model_path: ${model_path}
DTYPE: ${DTYPE}
SENSITIVE_LAYER_DTYPE: ${SENSITIVE_LAYER_DTYPE}
PROFILING_DEBUG_LEVEL: ${PROFILING_DEBUG_LEVEL}
==============================================================================
EOF
