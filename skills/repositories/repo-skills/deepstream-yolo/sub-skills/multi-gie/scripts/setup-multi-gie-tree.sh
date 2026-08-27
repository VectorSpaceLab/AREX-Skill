#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: setup-multi-gie-tree.sh --count N [--output-dir DIR] [--source-dir DIR]

Scaffold a self-contained multi-GIE runtime tree from the bundled DeepStream-
Yolo assets by default.

Defaults:
  source tree  -> bundled assets under this skill
  output dir   -> ./deepstream-yolo-multi-gie
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

BUNDLED_SOURCE="$SKILL_ROOT/assets/nvdsinfer_custom_impl_Yolo"
BUNDLED_CONFIGS="$SKILL_ROOT/assets/configs"
BUNDLED_IMAGES="$SKILL_ROOT/assets/images"

SOURCE_DIR="$BUNDLED_SOURCE"
OUTPUT_DIR="${PWD}/deepstream-yolo-multi-gie"
COUNT=""

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
    --count)
      COUNT=${2:?missing value for --count}
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

if [[ -z "$COUNT" ]]; then
  usage >&2
  exit 1
fi

if ! [[ "$COUNT" =~ ^[0-9]+$ ]] || [[ "$COUNT" -lt 2 ]]; then
  echo "--count must be an integer >= 2" >&2
  exit 1
fi

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

if [[ -d "$OUTPUT_DIR" ]] && [[ -n "$(find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Output dir exists and is not empty: $OUTPUT_DIR" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
cp -R "$BUNDLED_CONFIGS"/. "$OUTPUT_DIR"/
if [[ -d "$BUNDLED_IMAGES" ]]; then
  cp -R "$BUNDLED_IMAGES" "$OUTPUT_DIR"/
fi

for idx in $(seq 1 "$COUNT"); do
  gie_dir="$OUTPUT_DIR/gie$idx"
  mkdir -p "$gie_dir"
  cp -R "$SOURCE_DIR" "$gie_dir/"
  cp -R "$BUNDLED_CONFIGS"/config_infer_primary*.txt "$gie_dir/"
  cp -R "$BUNDLED_CONFIGS"/labels*.txt "$gie_dir/"
  cp "$BUNDLED_CONFIGS"/deepstream_app_config.txt "$gie_dir/"
  python - "$gie_dir" "$idx" <<'PY'
from pathlib import Path
import re
import sys

gie_dir = Path(sys.argv[1])
idx = int(sys.argv[2])
process_mode = 1 if idx == 1 else 2
prefix = f"gie{idx}/"

plugin = gie_dir / "nvdsinfer_custom_impl_Yolo" / "yoloPlugins.h"
if plugin.exists():
    text = plugin.read_text()
    text = re.sub(r'YOLOLAYER_PLUGIN_VERSION\s*\{\s*"[^"]+"\s*\}', f'YOLOLAYER_PLUGIN_VERSION {{"{idx}"}}', text)
    plugin.write_text(text)

path_keys = {
    "onnx-file",
    "custom-network-config",
    "model-file",
    "model-engine-file",
    "labelfile-path",
    "custom-lib-path",
}

def prefixed(value: str) -> str:
    value = value.strip()
    if not value or value.startswith(("/", "file:", "http:", "https:")):
        return value
    if value.startswith(prefix) or value.startswith("gie"):
        return value
    return prefix + value

for cfg in gie_dir.glob("config_infer_primary*.txt"):
    lines = cfg.read_text().splitlines()
    out = []
    saw_operate = False
    saw_class_ids = False
    inserted_after_process = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("gie-unique-id="):
            out.append(f"gie-unique-id={idx}")
            continue
        if stripped.startswith("process-mode="):
            out.append(f"process-mode={process_mode}")
            if idx > 1:
                out.append("operate-on-gie-id=1")
                out.append("operate-on-class-ids=0")
                saw_operate = True
                saw_class_ids = True
                inserted_after_process = True
            continue
        if stripped.startswith("operate-on-gie-id="):
            saw_operate = True
            if idx > 1:
                out.append("operate-on-gie-id=1")
            continue
        if stripped.startswith("operate-on-class-ids="):
            saw_class_ids = True
            if idx > 1:
                out.append("operate-on-class-ids=0")
            continue
        if "=" in stripped and not stripped.startswith("#"):
            key, value = stripped.split("=", 1)
            if key in path_keys:
                out.append(f"{key}={prefixed(value)}")
                continue
        out.append(line)
    if idx > 1 and not inserted_after_process:
        if not saw_operate:
            out.append("operate-on-gie-id=1")
        if not saw_class_ids:
            out.append("operate-on-class-ids=0")
    cfg.write_text("\n".join(out) + "\n")
PY
  echo "Created $gie_dir"
done

python - "$OUTPUT_DIR/deepstream_app_config.txt" "$COUNT" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
count = int(sys.argv[2])
text = path.read_text()
text = text.replace('config-file=config_infer_primary.txt', 'config-file=gie1/config_infer_primary.txt', 1)
sections = []
for idx in range(2, count + 1):
    sections.append(
        f'''[secondary-gie{idx - 2}]
enable=1
gpu-id=0
gie-unique-id={idx}
operate-on-gie-id=1
operate-on-class-ids=0
nvbuf-memory-type=0
config-file=gie{idx}/config_infer_primary.txt'''
    )
if sections:
    block = '\n\n' + '\n\n'.join(sections) + '\n'
    if '[tests]' in text:
        before, after = text.split('[tests]', 1)
        text = before.rstrip() + '\n\n' + block + '\n[tests]' + after
    else:
        text = text.rstrip() + '\n\n' + block
path.write_text(text)
PY

echo "Generated self-contained multi-GIE runtime tree at $OUTPUT_DIR"
echo "Root app config: $OUTPUT_DIR/deepstream_app_config.txt"
echo "Per-GIE source:  $OUTPUT_DIR/gieN/nvdsinfer_custom_impl_Yolo"
echo "Per-GIE configs: $OUTPUT_DIR/gieN/config_infer_primary*.txt"
if [[ -d "$OUTPUT_DIR/images" ]]; then
  echo "Illustration:    $OUTPUT_DIR/images/multipleGIEs_tree.png"
fi
