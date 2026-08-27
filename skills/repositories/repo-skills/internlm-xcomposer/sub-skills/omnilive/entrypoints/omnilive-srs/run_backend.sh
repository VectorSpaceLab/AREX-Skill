#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${ROOT_DIR:-${IXC_OMNILIVE_MODEL_ROOT:-}}"
if [[ -z "$ROOT_DIR" ]]; then
  echo "Set ROOT_DIR or IXC_OMNILIVE_MODEL_ROOT to the OmniLive model root." >&2
  exit 2
fi
export ROOT_DIR
export SRS_RTMP_BASE="${SRS_RTMP_BASE:-rtmp://127.0.0.1:1935/live/livestream}"
exec "$SCRIPT_DIR/backend_ixc/start.sh" "$@"
