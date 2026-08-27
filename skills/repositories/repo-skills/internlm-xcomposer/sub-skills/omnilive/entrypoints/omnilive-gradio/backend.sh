#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
MODEL_ROOT="${IXC_OMNILIVE_MODEL_ROOT:-${MODEL_ROOT:-internlm-xcomposer2d5-ol-7b}}"
export IXC_OMNILIVE_MODEL_ROOT="$MODEL_ROOT"
export IXC_OMNILIVE_BACKEND_BIND_HOST="${IXC_OMNILIVE_BACKEND_BIND_HOST:-}"
export IXC_OMNILIVE_ASR_PORT="${IXC_OMNILIVE_ASR_PORT:-8000}"
export IXC_OMNILIVE_LLM_PORT="${IXC_OMNILIVE_LLM_PORT:-8001}"
export IXC_OMNILIVE_VS_PORT="${IXC_OMNILIVE_VS_PORT:-8002}"
export IXC_OMNILIVE_ASR_HOST="${IXC_OMNILIVE_ASR_HOST:-}"
export IXC_OMNILIVE_VS_HOST="${IXC_OMNILIVE_VS_HOST:-}"
gpu_list="${CUDA_VISIBLE_DEVICES:-0}"
IFS=',' read -ra GPULIST <<< "$gpu_list"
echo "Using IXC_OMNILIVE_MODEL_ROOT=${IXC_OMNILIVE_MODEL_ROOT}"
echo "Running OmniLive Gradio backend trio on GPU list: ${gpu_list}"
echo "Ports: ASR=${IXC_OMNILIVE_ASR_PORT}, LLM=${IXC_OMNILIVE_LLM_PORT}, VS=${IXC_OMNILIVE_VS_PORT}"
cleanup() {
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT
CUDA_VISIBLE_DEVICES="${GPULIST[0]}" python backend_vs.py &
CUDA_VISIBLE_DEVICES="${GPULIST[0]}" python backend_llm.py &
CUDA_VISIBLE_DEVICES="${GPULIST[0]}" python backend.py
