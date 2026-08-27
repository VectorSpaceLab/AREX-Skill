#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

TARGET_ROOT="datasets"

usage() {
  cat <<'EOF'
Usage: download_euroc.sh [--target-root DIR]

Download the EuRoC MH_02_easy sample used by MonoGS into DIR/euroc/mh02.

Options:
  -t, --target-root DIR  Top-level dataset directory to create or reuse.
  -h, --help             Show this help text and exit.

The script creates directories only. Existing dataset directories are left
untouched.
EOF
}

log() {
  printf '%s\n' "$*"
}

fail() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "missing required command: $1"
}

normalize_euroc_tree() {
  local root="$1"

  if [[ -d "$root/mav0" ]]; then
    return 0
  fi

  local nested_dir
  nested_dir="$(find "$root" -mindepth 1 -maxdepth 1 -type d | head -n 1 || true)"
  [[ -n "$nested_dir" ]] || fail "expected $root/mav0 after extraction"

  if [[ -d "$nested_dir/mav0" ]]; then
    shopt -s dotglob nullglob
    mv "$nested_dir"/* "$root"/
    shopt -u dotglob nullglob
    rmdir "$nested_dir"
  fi

  [[ -d "$root/mav0" ]] || fail "expected $root/mav0 after normalizing the EuRoC archive"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--target-root)
      [[ $# -ge 2 ]] || fail "--target-root requires a value"
      TARGET_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

require_cmd wget
require_cmd unzip
require_cmd find
require_cmd mv
require_cmd rmdir

EUROC_ROOT="${TARGET_ROOT%/}/euroc"
EUROC_FINAL_DIR="$EUROC_ROOT/mh02"
EUROC_ARCHIVE="$EUROC_ROOT/MH_02_easy.zip"

if [[ -e "$EUROC_FINAL_DIR" ]]; then
  log "[skip] EuRoC already exists at $EUROC_FINAL_DIR"
  exit 0
fi

mkdir -p "$EUROC_ROOT"

if [[ ! -f "$EUROC_ARCHIVE" ]]; then
  log "[download] EuRoC MH_02_easy"
  wget -O "$EUROC_ARCHIVE" "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/machine_hall/MH_02_easy/MH_02_easy.zip"
else
  log "[reuse] MH_02_easy.zip already present"
fi

log "[extract] EuRoC MH_02_easy"
mkdir -p "$EUROC_FINAL_DIR"
unzip -q "$EUROC_ARCHIVE" -d "$EUROC_FINAL_DIR"
normalize_euroc_tree "$EUROC_FINAL_DIR"

log "Done."
