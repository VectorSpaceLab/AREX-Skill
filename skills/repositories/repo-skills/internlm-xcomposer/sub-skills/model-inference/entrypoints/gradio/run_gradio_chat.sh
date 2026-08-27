#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
MODEL="${MODEL:-internlm/internlm-xcomposer2d5-7b}"
PORT="${PORT:-7860}"
NUM_GPUS="${NUM_GPUS:-1}"
PRIVATE_FLAG=()
if [[ "${PRIVATE:-0}" == "1" || "${PRIVATE:-false}" == "true" ]]; then
  PRIVATE_FLAG=(--private)
fi
exec python gradio_demo/gradio_demo_chat.py --code_path "$MODEL" --num_gpus "$NUM_GPUS" --port "$PORT" "${PRIVATE_FLAG[@]}" "$@"
