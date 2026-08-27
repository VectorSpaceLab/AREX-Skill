#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
BACKEND_IP="${BACKEND_IP:-127.0.0.1}"
AUDIO_SOURCE="${AUDIO_SOURCE:-gradio}"
VIDEO_SOURCE="${VIDEO_SOURCE:-local}"
exec python frontend.py --backend_ip "$BACKEND_IP" --audio_source "$AUDIO_SOURCE" --video_source "$VIDEO_SOURCE" "$@"
