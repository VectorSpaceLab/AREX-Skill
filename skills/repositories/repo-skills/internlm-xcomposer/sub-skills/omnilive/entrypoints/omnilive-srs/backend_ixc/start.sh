#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
: "${ROOT_DIR:=${IXC_OMNILIVE_MODEL_ROOT:-}}"
if [[ -z "$ROOT_DIR" ]]; then
  echo "Set ROOT_DIR or IXC_OMNILIVE_MODEL_ROOT to the OmniLive model root containing audio/, memory/, and merge_lora/." >&2
  exit 2
fi
export ROOT_DIR
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-7862}"
exec uvicorn main:app --host "$HOST" --port "$PORT" --loop asyncio "$@"
