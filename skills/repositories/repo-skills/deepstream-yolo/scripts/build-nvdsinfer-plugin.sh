#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: build-nvdsinfer-plugin.sh [--output-dir DIR] [--source-dir DIR] [--stage-only]

Stage the bundled DeepStream-Yolo assets into a runtime directory, optionally
overlay a replacement parser source tree, then build the custom shared library
there.

Defaults:
  source tree  -> bundled assets under this skill
  output dir   -> ./deepstream-yolo-runtime
EOF
}

find_skill_root() {
  local dir="$1"
  while [[ "$dir" != "/" ]]; do
    if [[ -d "$dir/assets/nvdsinfer_custom_impl_Yolo" && -f "$dir/scripts/stage-runtime-tree.sh" ]]; then
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

BUNDLED_SOURCE="$SKILL_ROOT/assets/nvdsinfer_custom_impl_Yolo"
STAGE_HELPER="$SKILL_ROOT/scripts/stage-runtime-tree.sh"

SOURCE_DIR="$BUNDLED_SOURCE"
OUTPUT_DIR="${PWD}/deepstream-yolo-runtime"
STAGE_ONLY=0
OPENCV=${OPENCV:-0}
GRAPH=${GRAPH:-0}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-dir)
      SOURCE_DIR=${2:?missing value for --source-dir}
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR=${2:?missing value for --output-dir}
      shift 2
      ;;
    --stage-only)
      STAGE_ONLY=1
      shift
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

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Source tree not found: $SOURCE_DIR" >&2
  exit 1
fi
if [[ -d "$SOURCE_DIR/nvdsinfer_custom_impl_Yolo" && ! -f "$SOURCE_DIR/Makefile" ]]; then
  SOURCE_DIR="$SOURCE_DIR/nvdsinfer_custom_impl_Yolo"
fi
if [[ ! -f "$SOURCE_DIR/Makefile" ]]; then
  echo "Source tree must be the bundled parser directory or a directory containing nvdsinfer_custom_impl_Yolo/Makefile: $SOURCE_DIR" >&2
  exit 1
fi

if [[ "$STAGE_ONLY" != "1" && -z "${CUDA_VER:-}" ]]; then
  echo "CUDA_VER is required. Example: CUDA_VER=12.8 $0 --output-dir ./deepstream-yolo-runtime" >&2
  exit 1
fi

if [[ -d "$OUTPUT_DIR" ]] && [[ -n "$(find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output dir exists and is not empty: $OUTPUT_DIR" >&2
  exit 1
fi

"$STAGE_HELPER" --output-dir "$OUTPUT_DIR"
if [[ "$SOURCE_DIR" != "$BUNDLED_SOURCE" ]]; then
  rm -rf "$OUTPUT_DIR/nvdsinfer_custom_impl_Yolo"
  cp -R "$SOURCE_DIR" "$OUTPUT_DIR/nvdsinfer_custom_impl_Yolo"
fi

if [[ "$STAGE_ONLY" == "1" ]]; then
  echo "Stage-only requested; skipping make."
  exit 0
fi

echo "Building custom library in $OUTPUT_DIR/nvdsinfer_custom_impl_Yolo"
echo "  CUDA_VER=$CUDA_VER"
echo "  OPENCV=$OPENCV"
echo "  GRAPH=$GRAPH"

make -C "$OUTPUT_DIR/nvdsinfer_custom_impl_Yolo" clean
make -C "$OUTPUT_DIR/nvdsinfer_custom_impl_Yolo" OPENCV="$OPENCV" GRAPH="$GRAPH"

echo "Done."
echo "Runtime tree: $OUTPUT_DIR"
echo "Library: $OUTPUT_DIR/nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so"
