#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/Frontend"
export VITE_CHAT_SOCKET_URL="${VITE_CHAT_SOCKET_URL:-ws://localhost:7862/chat}"
export VITE_SRS_BASE_URL="${VITE_SRS_BASE_URL:-webrtc://localhost/live/livestream}"
export VITE_SRS_API_URL="${VITE_SRS_API_URL:-http://localhost:1985}"
exec npm run start -- "$@"
