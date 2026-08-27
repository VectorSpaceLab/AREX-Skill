#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: make-calibration-list.sh IMAGE_DIR [OUTPUT_FILE]

Write absolute image paths to OUTPUT_FILE for INT8 calibration.
EOF
}

if [[ ${1:-} == "" || ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  [[ ${1:-} == "" ]] && exit 1 || exit 0
fi

IMAGE_DIR=$1
OUTPUT_FILE=${2:-calibration.txt}

if [[ ! -d "$IMAGE_DIR" ]]; then
  echo "Image directory not found: $IMAGE_DIR" >&2
  exit 1
fi

shopt -s nullglob
images=("$IMAGE_DIR"/*.{jpg,jpeg,png,bmp,webp})
if [[ ${#images[@]} -eq 0 ]]; then
  echo "No image files found in $IMAGE_DIR" >&2
  exit 1
fi

: > "$OUTPUT_FILE"
for img in "${images[@]}"; do
  realpath "$img" >> "$OUTPUT_FILE"
done

echo "Wrote ${#images[@]} image paths to $OUTPUT_FILE"
