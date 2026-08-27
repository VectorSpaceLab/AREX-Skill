#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_ROOT="${IXC_OMNILIVE_MODEL_ROOT:-${MODEL_ROOT:-internlm-xcomposer2d5-ol-7b}}"
export IXC_OMNILIVE_MODEL_ROOT="$MODEL_ROOT"
exec python "$SCRIPT_DIR/infer_llm_with_memory.py" --ixc-model-path "$MODEL_ROOT" "$@"
