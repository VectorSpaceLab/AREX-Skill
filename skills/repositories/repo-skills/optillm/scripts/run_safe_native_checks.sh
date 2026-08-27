#!/usr/bin/env bash
# Run a bounded set of OptiLLM native checks when a source checkout is available.
# This helper is optional: the runtime skill does not require the original checkout.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run_safe_native_checks.sh [--repo-root PATH] [--python PYTHON] [--pytest-args ARGS]

Runs selected CPU-safe OptiLLM tests that avoid real provider calls, browser
sessions, model downloads, and benchmark-scale workloads.

Examples:
  bash run_safe_native_checks.sh --repo-root /path/to/optillm
  bash run_safe_native_checks.sh --repo-root . --pytest-args "-q --tb=short"
EOF
}

REPO_ROOT="."
PYTHON_BIN="python"
PYTEST_ARGS="-q --tb=short"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root) REPO_ROOT="$2"; shift 2 ;;
    --python) PYTHON_BIN="$2"; shift 2 ;;
    --pytest-args) PYTEST_ARGS="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! -f "$REPO_ROOT/pyproject.toml" || ! -d "$REPO_ROOT/optillm" ]]; then
  echo "Not an OptiLLM source checkout: $REPO_ROOT" >&2
  exit 2
fi

cd "$REPO_ROOT"
"$PYTHON_BIN" - <<'PY'
import importlib.util
missing = [name for name in ["pytest", "optillm"] if importlib.util.find_spec(name) is None]
if missing:
    raise SystemExit("Missing required import(s): " + ", ".join(missing) + ". Install OptiLLM and pytest first.")
import optillm
print("optillm", getattr(optillm, "__version__", "unknown"))
PY

# Keep this list conservative. Full API/server tests can require local model
# downloads or provider credentials and should be run only after explicit setup.
TESTS=(
  "tests/test_approaches.py"
  "tests/test_reasoning_simple.py"
  "tests/test_mcp_plugin.py"
)

for test_file in "${TESTS[@]}"; do
  if [[ -f "$test_file" ]]; then
    echo "==> $test_file"
    # shellcheck disable=SC2086
    "$PYTHON_BIN" -m pytest "$test_file" $PYTEST_ARGS
  else
    echo "Skipping missing $test_file"
  fi
done
