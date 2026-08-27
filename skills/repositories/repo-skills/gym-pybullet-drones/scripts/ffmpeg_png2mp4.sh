#!/usr/bin/env bash
set -euo pipefail

# Convert a PNG frame sequence into an H.264 MP4.
#
# Safe defaults:
# - reads only local PNG frames
# - writes one output file
# - refuses to overwrite unless --force is passed
#
# Usage examples:
#   bash scripts/ffmpeg_png2mp4.sh --input-pattern 'frame_%d.png' --output-file video.mp4
#   FRAME_RATE=30 RESOLUTION=1280x720 bash scripts/ffmpeg_png2mp4.sh --output-file /tmp/video.mp4

show_help() {
  cat <<'EOF'
Usage: ffmpeg_png2mp4.sh [options]

Options:
  --input-pattern PATTERN   Frame glob/pattern for ffmpeg image2 input.
                            Default: frame_%d.png
  --output-file FILE        MP4 output path. Default: video.mp4
  --frame-rate FPS          Input frame rate. Default: 24
  --resolution WxH          Input frame size. Default: 640x480
  --force                   Overwrite output file if it exists.
  -h, --help                Show this help.

Environment overrides:
  FRAME_RATE, RESOLUTION, INPUT_PATTERN, OUTPUT_FILE
EOF
}

FRAME_RATE="${FRAME_RATE:-24}"
RESOLUTION="${RESOLUTION:-640x480}"
INPUT_PATTERN="${INPUT_PATTERN:-frame_%d.png}"
OUTPUT_FILE="${OUTPUT_FILE:-video.mp4}"
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input-pattern)
      INPUT_PATTERN="${2:?missing value for --input-pattern}"
      shift 2
      ;;
    --output-file)
      OUTPUT_FILE="${2:?missing value for --output-file}"
      shift 2
      ;;
    --frame-rate)
      FRAME_RATE="${2:?missing value for --frame-rate}"
      shift 2
      ;;
    --resolution)
      RESOLUTION="${2:?missing value for --resolution}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      show_help >&2
      exit 2
      ;;
  esac
done

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is not on PATH; install ffmpeg before using this helper." >&2
  exit 1
fi

if [[ -e "$OUTPUT_FILE" && "$FORCE" -ne 1 ]]; then
  echo "Output file already exists: $OUTPUT_FILE (pass --force to overwrite)." >&2
  exit 1
fi

ffmpeg -y \
  -r "$FRAME_RATE" \
  -f image2 \
  -s "$RESOLUTION" \
  -i "$INPUT_PATTERN" \
  -vcodec libx264 \
  -crf 25 \
  -pix_fmt yuv420p \
  "$OUTPUT_FILE"
