#!/usr/bin/env bash
# Build SiamMask's local Cython extensions with an explicit Python executable.
# This helper adapts the repository's make.sh and optional COCO pycocotools build.
# It performs only local build_ext --inplace operations; it does not download data
# or install packages.

set -euo pipefail

REPO_ROOT="${PWD}"
PYTHON_BIN="${PYTHON:-python}"
WITH_COCO=1
DRY_RUN=0

show_help() {
  cat <<'EOF'
Usage: build_extensions.sh [--repo-root PATH] [--python PYTHON] [--no-coco] [--dry-run]

Builds the local Cython extensions needed by SiamMask tracking/evaluation:
  - utils/pyvotkit/region
  - utils/pysot/utils/region
  - data/coco/pycocotools/_mask (unless --no-coco)

Examples:
  ./scripts/build_extensions.sh --repo-root /path/to/SiamMask --python /path/to/env/bin/python
  ./scripts/build_extensions.sh --repo-root /path/to/SiamMask --dry-run
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$2"; shift 2 ;;
    --python)
      PYTHON_BIN="$2"; shift 2 ;;
    --no-coco)
      WITH_COCO=0; shift ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    -h|--help)
      show_help; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      show_help >&2
      exit 2 ;;
  esac
done

REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"

run_build() {
  local rel="$1"
  local dir="$REPO_ROOT/$rel"
  if [[ ! -f "$dir/setup.py" ]]; then
    echo "Missing setup.py in $rel" >&2
    return 1
  fi
  echo "[build] $rel using $PYTHON_BIN"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "(dry-run) cd '$dir' && '$PYTHON_BIN' setup.py build_ext --inplace"
  else
    (cd "$dir" && "$PYTHON_BIN" setup.py build_ext --inplace)
  fi
}

run_build "utils/pyvotkit"
run_build "utils/pysot/utils"
if [[ "$WITH_COCO" -eq 1 ]]; then
  run_build "data/coco/pycocotools"
fi

echo "done"
