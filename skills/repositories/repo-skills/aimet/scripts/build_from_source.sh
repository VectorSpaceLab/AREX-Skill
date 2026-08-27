#!/usr/bin/env bash
# Safe source-build adapter for AIMET. Run inside a dedicated Python env.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: build_from_source.sh [options]

Options:
  --repo-dir DIR      AIMET checkout to build (default: current directory)
  --torch-only        Build AIMET Torch only
  --onnx-only         Build AIMET ONNX only
  --both              Build both Torch and ONNX (default)
  --cuda              Enable CUDA build
  --no-cuda           Disable CUDA build (default)
  --clean             Remove the checkout build/ directory first
  --skip-smoke        Do not run quick_smoke.py after install
  --dry-run           Print commands without executing
  -h, --help          Show this help

This script does not install system packages. For CUDA builds it expects nvcc
and a compatible compiler/toolchain to already be available.
EOF
}

REPO_DIR="$PWD"
ENABLE_TORCH=ON
ENABLE_ONNX=ON
ENABLE_CUDA=OFF
CLEAN=0
RUN_SMOKE=1
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-dir) REPO_DIR="$2"; shift 2 ;;
    --torch-only) ENABLE_TORCH=ON; ENABLE_ONNX=OFF; shift ;;
    --onnx-only) ENABLE_TORCH=OFF; ENABLE_ONNX=ON; shift ;;
    --both) ENABLE_TORCH=ON; ENABLE_ONNX=ON; shift ;;
    --cuda) ENABLE_CUDA=ON; shift ;;
    --no-cuda) ENABLE_CUDA=OFF; shift ;;
    --clean) CLEAN=1; shift ;;
    --skip-smoke) RUN_SMOKE=0; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

REPO_DIR="$(cd "$REPO_DIR" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$REPO_DIR/pyproject.toml" || ! -d "$REPO_DIR/TrainingExtensions" ]]; then
  echo "ERROR: --repo-dir does not look like an AIMET checkout: $REPO_DIR" >&2
  exit 2
fi

if [[ "$ENABLE_CUDA" == "ON" ]] && ! command -v nvcc >/dev/null 2>&1; then
  echo "ERROR: CUDA build requested but nvcc was not found." >&2
  echo "Use --no-cuda for CPU builds or run inside a CUDA development image." >&2
  exit 2
fi

run_cmd() {
  printf '+ %q' "$@"; echo
  if [[ "$DRY_RUN" == "0" ]]; then
    "$@"
  fi
}

CMAKE_ARGS="-DENABLE_CUDA=$ENABLE_CUDA -DENABLE_TORCH=$ENABLE_TORCH -DENABLE_ONNX=$ENABLE_ONNX"

echo "AIMET source build"
echo "  repo:        $REPO_DIR"
echo "  CMAKE_ARGS:  $CMAKE_ARGS"
echo "  python:      $(python -c 'import sys; print(sys.executable)')"

if [[ "$CLEAN" == "1" ]]; then
  run_cmd rm -rf "$REPO_DIR/build"
fi

run_cmd python -m pip install "scikit-build-core[wheels]==0.11.1" build pybind11 "cython>=3.0"
(
  cd "$REPO_DIR"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "+ CMAKE_ARGS=$CMAKE_ARGS python -m pip install --no-build-isolation -e $REPO_DIR"
  else
    CMAKE_ARGS="$CMAKE_ARGS" python -m pip install --no-build-isolation -e "$REPO_DIR"
  fi
)
run_cmd python -m pip check

if [[ "$RUN_SMOKE" == "1" ]]; then
  FRAMEWORK="both"
  if [[ "$ENABLE_TORCH" == "ON" && "$ENABLE_ONNX" == "OFF" ]]; then FRAMEWORK="torch"; fi
  if [[ "$ENABLE_TORCH" == "OFF" && "$ENABLE_ONNX" == "ON" ]]; then FRAMEWORK="onnx"; fi
  run_cmd python "$SCRIPT_DIR/quick_smoke.py" --framework "$FRAMEWORK"
fi
