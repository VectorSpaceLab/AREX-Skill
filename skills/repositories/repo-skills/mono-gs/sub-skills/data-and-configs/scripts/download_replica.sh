#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

TARGET_ROOT="datasets"

usage() {
  cat <<'EOF'
Usage: download_replica.sh [--target-root DIR]

Download the Replica dataset zip used by MonoGS into DIR/replica.

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
require_cmd mv

REPLICA_PARENT="${TARGET_ROOT%/}"
REPLICA_ARCHIVE="$REPLICA_PARENT/Replica.zip"
REPLICA_FINAL_DIR="$REPLICA_PARENT/replica"
REPLICA_STAGING_DIR="$REPLICA_PARENT/Replica"

if [[ -e "$REPLICA_FINAL_DIR" ]]; then
  log "[skip] Replica already exists at $REPLICA_FINAL_DIR"
  exit 0
fi

if [[ -e "$REPLICA_STAGING_DIR" ]]; then
  fail "staging directory $REPLICA_STAGING_DIR already exists; inspect or move it manually before rerunning"
fi

mkdir -p "$REPLICA_PARENT"

if [[ ! -f "$REPLICA_ARCHIVE" ]]; then
  log "[download] Replica"
  wget -O "$REPLICA_ARCHIVE" "https://cvg-data.inf.ethz.ch/nice-slam/data/Replica.zip"
else
  log "[reuse] Replica.zip already present"
fi

log "[extract] Replica"
unzip -q "$REPLICA_ARCHIVE" -d "$REPLICA_PARENT"

if [[ -d "$REPLICA_STAGING_DIR" ]]; then
  mv "$REPLICA_STAGING_DIR" "$REPLICA_FINAL_DIR"
elif [[ -d "$REPLICA_FINAL_DIR" ]]; then
  log "[ok] archive created $REPLICA_FINAL_DIR directly"
else
  fail "could not locate extracted Replica directory under $REPLICA_PARENT"
fi

log "Done."
