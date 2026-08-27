#!/usr/bin/env bash
# Build helper for PointNet2's visualization renderer (utils/render_balls_so.cpp).
# This does NOT compile TensorFlow custom ops.
set -euo pipefail

repo_root=""
source_dir=""
out_dir=""
cxx="${CXX:-g++}"
std="c++11"
abi="0"
dry_run="0"
extra_flags=()

usage() {
  cat <<'USAGE'
Usage: compile_render_balls_so.sh [OPTIONS]

Build utils/render_balls_so.cpp into render_balls_so.so for utils/show3d_balls.py.
This helper is intentionally scoped to the OpenCV/ctypes visualization renderer;
it does not build tf_sampling_so.so, tf_grouping_so.so, or tf_interpolate_so.so.

Options:
  --repo-root PATH   Path to the pointnet2 checkout. Used to infer utils/.
  --source-dir PATH  Directory containing render_balls_so.cpp. Overrides --repo-root inference.
  --out-dir PATH     Output directory for render_balls_so.so. Default: source dir.
  --cxx PATH         C++ compiler. Default: ${CXX:-g++}.
  --std STD          C++ standard. Default: c++11.
  --abi 0|1          _GLIBCXX_USE_CXX11_ABI value. Source recipe used 0.
  --extra FLAG       Extra compiler/linker flag; may be repeated.
  --dry-run          Print the command but do not execute it.
  -h, --help         Show this help.

Examples:
  bash scripts/compile_render_balls_so.sh --repo-root /path/to/pointnet2 --dry-run
  bash scripts/compile_render_balls_so.sh --repo-root /path/to/pointnet2 --out-dir /path/to/pointnet2/utils
USAGE
}

find_repo_root() {
  local start="$PWD"
  while [[ "$start" != "/" ]]; do
    if [[ -f "$start/utils/render_balls_so.cpp" ]]; then
      printf '%s\n' "$start"
      return 0
    fi
    start="$(dirname "$start")"
  done
  return 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      repo_root="$2"; shift 2 ;;
    --source-dir)
      source_dir="$2"; shift 2 ;;
    --out-dir)
      out_dir="$2"; shift 2 ;;
    --cxx)
      cxx="$2"; shift 2 ;;
    --std)
      std="$2"; shift 2 ;;
    --abi)
      abi="$2"; shift 2 ;;
    --extra)
      extra_flags+=("$2"); shift 2 ;;
    --dry-run)
      dry_run="1"; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2 ;;
  esac
done

if [[ -z "$source_dir" ]]; then
  if [[ -n "$repo_root" ]]; then
    source_dir="$repo_root/utils"
  else
    if inferred="$(find_repo_root)"; then
      source_dir="$inferred/utils"
    else
      echo "Could not infer source dir. Pass --repo-root or --source-dir." >&2
      exit 2
    fi
  fi
fi

if [[ -z "$out_dir" ]]; then
  out_dir="$source_dir"
fi

if [[ "$abi" != "0" && "$abi" != "1" ]]; then
  echo "--abi must be 0 or 1" >&2
  exit 2
fi

src="$source_dir/render_balls_so.cpp"
out="$out_dir/render_balls_so.so"

if [[ ! -f "$src" ]]; then
  echo "Missing renderer source: $src" >&2
  exit 1
fi

if ! command -v "$cxx" >/dev/null 2>&1; then
  echo "C++ compiler not found: $cxx" >&2
  exit 1
fi

mkdir -p "$out_dir"
cmd=("$cxx" "-std=$std" "$src" "-o" "$out" "-shared" "-fPIC" "-O2" "-D_GLIBCXX_USE_CXX11_ABI=$abi")
if [[ ${#extra_flags[@]} -gt 0 ]]; then
  cmd+=("${extra_flags[@]}")
fi

echo "Renderer compile command:"
printf ' %q' "${cmd[@]}"
printf '\n'

if [[ "$dry_run" == "1" ]]; then
  echo "Dry run only; not compiling."
  exit 0
fi

"${cmd[@]}"
if [[ -f "$out" ]]; then
  echo "Built: $out"
else
  echo "Compile command exited successfully but output is missing: $out" >&2
  exit 1
fi
