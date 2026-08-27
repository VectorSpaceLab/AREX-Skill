#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: run_cpp_smoke.sh --include-dir DIR [--cxx COMPILER]

Compile and run the bundled C++11 smoke program against the public hnswlib
headers. The wrapper creates a temporary build directory and persistence file,
then removes both when it exits.
EOF
}

include_dir=""
cxx="${CXX:-c++}"

while (($# > 0)); do
    case "$1" in
        --help|-h)
            usage
            exit 0
            ;;
        --include-dir)
            if (($# < 2)); then
                echo "error: --include-dir needs a value" >&2
                usage >&2
                exit 2
            fi
            include_dir="$2"
            shift 2
            ;;
        --cxx)
            if (($# < 2)); then
                echo "error: --cxx needs a value" >&2
                usage >&2
                exit 2
            fi
            cxx="$2"
            shift 2
            ;;
        *)
            echo "error: unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [[ -z "$include_dir" ]]; then
    echo "error: an explicit --include-dir is required" >&2
    usage >&2
    exit 2
fi

if [[ ! -d "$include_dir/hnswlib" || ! -f "$include_dir/hnswlib/hnswlib.h" ]]; then
    echo "error: --include-dir must contain hnswlib/hnswlib.h" >&2
    exit 2
fi

if ! command -v "$cxx" >/dev/null 2>&1; then
    echo "error: compiler not found: $cxx" >&2
    exit 127
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
tmp_dir="$(mktemp -d)"
cleanup() {
    rm -rf -- "$tmp_dir"
}
trap cleanup EXIT INT TERM

"$cxx" \
    -std=c++11 \
    -O2 \
    -Wall \
    -Wextra \
    -Wpedantic \
    -pthread \
    -I"$include_dir" \
    "$script_dir/cpp_smoke.cpp" \
    -o "$tmp_dir/cpp_smoke"

"$tmp_dir/cpp_smoke" "$tmp_dir/index.bin"
