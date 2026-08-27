#!/usr/bin/env bash
# Read-only smoke test for the Anomalib CLI help surface.
#
# This helper checks the top-level router, install help, verbose help behavior,
# and export flags without running training, inference, or installation.
#
# Example:
#   ./check_cli_help.sh --python /path/to/python

set -euo pipefail

python_bin="${PYTHON_BIN:-python}"
require_benchmark=0

usage() {
  cat <<'EOF'
Usage: check_cli_help.sh [--python PATH] [--require-benchmark]

Options:
  --python PATH         Python interpreter used to run `python -m anomalib.cli.cli`.
  --require-benchmark   Fail if the top-level help does not expose benchmark.
  -h, --help            Show this help and exit.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      if [[ $# -lt 2 ]]; then
        echo "--python requires a path" >&2
        exit 2
      fi
      python_bin="$2"
      shift 2
      ;;
    --require-benchmark)
      require_benchmark=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

run_cli() {
  "$python_bin" -m anomalib.cli.cli "$@" 2>&1
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  if ! grep -Fq -- "$needle" <<<"$haystack"; then
    printf 'expected help output to contain: %s\n' "$needle" >&2
    exit 1
  fi
}

assert_not_contains() {
  local haystack="$1"
  local needle="$2"
  if grep -Fq -- "$needle" <<<"$haystack"; then
    printf 'did not expect help output to contain: %s\n' "$needle" >&2
    exit 1
  fi
}

check_python() {
  if ! "$python_bin" -V >/dev/null 2>&1; then
    echo "Python interpreter '$python_bin' is not usable. Pass --python to a Python that has Anomalib installed." >&2
    exit 1
  fi
}

openvino_importable() {
  "$python_bin" - <<'PY'
import importlib.util
raise SystemExit(0 if importlib.util.find_spec('openvino') is not None else 1)
PY
}

diagnose_cli_failure() {
  local output="$1"
  if grep -Eq 'No module named (anomalib|lightning|openvino)|ModuleNotFoundError|ImportError' <<<"$output"; then
    if grep -Fq 'No module named anomalib' <<<"$output" || grep -Fq 'ModuleNotFoundError: No module named '\''anomalib'\''' <<<"$output"; then
      echo "Anomalib is not importable in '$python_bin'. Install the package or pass --python to the environment that has it." >&2
    elif grep -Fq 'No module named lightning' <<<"$output" || grep -Fq 'ModuleNotFoundError: No module named '\''lightning'\''' <<<"$output"; then
      echo "Lightning is missing. Install the CPU package extra, for example: uv pip install \"anomalib[cpu]\" or pip install \"anomalib[cpu]\"." >&2
    elif grep -Fq 'No module named openvino' <<<"$output" || grep -Fq 'ModuleNotFoundError: No module named '\''openvino'\''' <<<"$output"; then
      echo "OpenVINO is missing. Add the OpenVINO extra, for example: uv pip install \"anomalib[cpu,openvino]\" or pip install \"anomalib[cpu,openvino]\"." >&2
    else
      echo "$output" >&2
    fi
  else
    echo "$output" >&2
  fi
  exit 1
}

check_python

if ! top_help="$(run_cli --help)"; then
  diagnose_cli_failure "$top_help"
fi
if ! install_help="$(run_cli install --help)"; then
  diagnose_cli_failure "$install_help"
fi
if ! train_help_v="$(run_cli train -h -v)"; then
  diagnose_cli_failure "$train_help_v"
fi
if ! train_help_vv="$(run_cli train -h -vv)"; then
  diagnose_cli_failure "$train_help_vv"
fi
if ! export_help="$(run_cli export --help)"; then
  diagnose_cli_failure "$export_help"
fi

for command in install fit validate test train predict export; do
  assert_contains "$top_help" "$command"
done

if grep -Fq -- "benchmark" <<<"$top_help"; then
  assert_contains "$top_help" "benchmark"
elif [[ "$require_benchmark" -eq 1 ]]; then
  echo "benchmark is missing from top-level help" >&2
  exit 1
else
  echo "benchmark is not present in top-level help; skipping the benchmark assertion." >&2
fi

assert_contains "$top_help" "--config"
assert_contains "$top_help" "--print_config"
assert_contains "$install_help" "full,core,dev,loggers,notebooks,openvino"
assert_contains "$install_help" "-v, --verbose"
assert_contains "$train_help_v" "Quick-Start"
assert_contains "$train_help_v" "Arguments"
assert_contains "$train_help_vv" "Arguments"
assert_not_contains "$train_help_vv" "Quick-Start"

if openvino_importable; then
  assert_contains "$export_help" "--input_size"
  assert_contains "$export_help" "--compression_type"
fi

printf 'CLI help smoke passed.\n'
