#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

TARGET_ROOT="datasets"

usage() {
  cat <<'EOF'
Usage: download_tum.sh [--target-root DIR]

Download the TUM RGB-D sample sequences used by MonoGS into DIR/tum.

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

download_and_extract() {
  local scene_label="$1"
  local archive_name="$2"
  local url="$3"
  local final_dir="$4"
  local archive_path="$TUM_ROOT/$archive_name"

  if [[ -e "$final_dir" ]]; then
    log "[skip] $scene_label already exists at $final_dir"
    return 0
  fi

  mkdir -p "$TUM_ROOT"

  if [[ ! -f "$archive_path" ]]; then
    log "[download] $scene_label"
    wget -O "$archive_path" "$url"
  else
    log "[reuse] $archive_name already present"
  fi

  log "[extract] $scene_label"
  tar -xzf "$archive_path" -C "$TUM_ROOT"

  [[ -d "$final_dir" ]] || fail "expected $final_dir after extracting $archive_name"
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
require_cmd tar

TUM_ROOT="${TARGET_ROOT%/}/tum"

log "Using target root: $TUM_ROOT"
mkdir -p "$TUM_ROOT"

download_and_extract \
  "TUM fr1_desk" \
  "rgbd_dataset_freiburg1_desk.tgz" \
  "https://vision.in.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_desk.tgz" \
  "$TUM_ROOT/rgbd_dataset_freiburg1_desk"

download_and_extract \
  "TUM fr2_xyz" \
  "rgbd_dataset_freiburg2_xyz.tgz" \
  "https://vision.in.tum.de/rgbd/dataset/freiburg2/rgbd_dataset_freiburg2_xyz.tgz" \
  "$TUM_ROOT/rgbd_dataset_freiburg2_xyz"

download_and_extract \
  "TUM fr3_office" \
  "rgbd_dataset_freiburg3_long_office_household.tgz" \
  "https://vision.in.tum.de/rgbd/dataset/freiburg3/rgbd_dataset_freiburg3_long_office_household.tgz" \
  "$TUM_ROOT/rgbd_dataset_freiburg3_long_office_household"

log "Done."
