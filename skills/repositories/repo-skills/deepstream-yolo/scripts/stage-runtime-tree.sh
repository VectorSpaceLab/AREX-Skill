#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: stage-runtime-tree.sh [--output-dir DIR]

Stage the bundled DeepStream-Yolo assets into a fresh runtime directory.
Copies:
  - assets/nvdsinfer_custom_impl_Yolo/
  - assets/configs/
  - assets/images/
EOF
}

find_skill_root() {
  local dir="$1"
  while [[ "$dir" != "/" ]]; do
    if [[ -d "$dir/assets/nvdsinfer_custom_impl_Yolo" && -d "$dir/assets/configs" ]]; then
      printf '%s\n' "$dir"
      return 0
    fi
    dir=$(dirname "$dir")
  done
  return 1
}

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SKILL_ROOT=$(find_skill_root "$SCRIPT_DIR") || {
  echo "Could not locate bundled DeepStream-Yolo assets from $SCRIPT_DIR" >&2
  exit 1
}

OUTPUT_DIR="${PWD}/deepstream-yolo-runtime"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir)
      OUTPUT_DIR=${2:?missing value for --output-dir}
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -d "$OUTPUT_DIR" ]] && [[ -n "$(find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output dir exists and is not empty: $OUTPUT_DIR" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
cp -R "$SKILL_ROOT/assets/configs"/. "$OUTPUT_DIR"/
if [[ -d "$SKILL_ROOT/assets/images" ]]; then
  cp -R "$SKILL_ROOT/assets/images" "$OUTPUT_DIR"/
fi
cp -R "$SKILL_ROOT/assets/nvdsinfer_custom_impl_Yolo" "$OUTPUT_DIR/"

echo "Staged runtime tree at $OUTPUT_DIR"
echo "  configs: $OUTPUT_DIR/config_infer_primary*.txt and $OUTPUT_DIR/deepstream_app_config.txt"
echo "  labels:  $OUTPUT_DIR/labels*.txt"
echo "  parser:  $OUTPUT_DIR/nvdsinfer_custom_impl_Yolo"
if [[ -d "$OUTPUT_DIR/images" ]]; then
  echo "  images:  $OUTPUT_DIR/images"
fi
