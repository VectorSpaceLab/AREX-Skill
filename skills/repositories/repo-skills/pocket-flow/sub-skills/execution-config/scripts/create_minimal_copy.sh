#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
usage: create_minimal_copy.sh SOURCE_DIR TARGET_DIR [--force] [--dry-run]

Create a minimal isolated copy of a PocketFlow checkout.
  --force    replace an existing target directory
  --dry-run  print the planned action without copying
EOF
}

abspath() {
  python - "$1" <<'PY'
import os
import sys
print(os.path.realpath(sys.argv[1]))
PY
}

dry_run=0
force=0
src=""
dst=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)
      dry_run=1
      ;;
    --force)
      force=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [ -z "$src" ]; then
        src="$1"
      elif [ -z "$dst" ]; then
        dst="$1"
      else
        echo "unexpected extra argument: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
  shift
done

if [ -z "$src" ] || [ -z "$dst" ]; then
  usage >&2
  exit 2
fi
if [ ! -d "$src" ]; then
  echo "source directory not found: $src" >&2
  exit 1
fi

src_abs="$(abspath "$src")"
dst_abs="$(abspath "$dst")"

if [ "$src_abs" = "$dst_abs" ]; then
  echo "source and target must be different: $src_abs" >&2
  exit 2
fi
case "$dst_abs/" in
  "$src_abs"/*)
    echo "target must not be inside source tree: $dst_abs" >&2
    exit 2
    ;;
esac

if [ -e "$dst_abs" ] && [ "$force" -ne 1 ] && [ "$dry_run" -ne 1 ]; then
  echo "target already exists: $dst_abs (use --force to replace it)" >&2
  exit 2
fi

if [ "$dry_run" -eq 1 ]; then
  echo "source=$src_abs"
  echo "target=$dst_abs"
  echo "action=copy"
  if [ -e "$dst_abs" ]; then
    echo "note=target exists; add --force to replace it"
  fi
  echo "excludes=.git,.gitignore,logs,models*,__pycache__,*.pyc"
  exit 0
fi

if [ -e "$dst_abs" ] && [ "$force" -eq 1 ]; then
  rm -rf "$dst_abs"
fi

mkdir -p "$(dirname "$dst_abs")"

if command -v rsync >/dev/null 2>&1; then
  mkdir -p "$dst_abs"
  rsync -a --delete \
    --exclude='.git/' \
    --exclude='.gitignore' \
    --exclude='logs/' \
    --exclude='models*' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    "$src_abs"/ "$dst_abs"/
else
  cp -a "$src_abs" "$dst_abs"
  rm -rf "$dst_abs/.git" "$dst_abs/.gitignore" "$dst_abs/logs" "$dst_abs"/models* "$dst_abs"/__pycache__
  find "$dst_abs" -name '*.pyc' -delete
fi

echo "created minimal copy: $dst_abs"
