#!/usr/bin/env bash
set -euo pipefail

# Launch GPT Academic from a checkout root.
# Usage: PYTHON=/path/to/python scripts/launch_app.sh --repo-root <checkout> [main.py args]

PYTHON_BIN="${PYTHON:-python}"
REPO_ROOT=""
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="${2:-}"
      shift 2
      ;;
    --repo-root=*)
      REPO_ROOT="${1#--repo-root=}"
      shift
      ;;
    -h|--help)
      echo "Usage: PYTHON=python $0 --repo-root <gpt_academic_checkout> [main.py args]"
      exit 0
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ -z "$REPO_ROOT" ]]; then
  REPO_ROOT="$PWD"
fi
if [[ ! -f "$REPO_ROOT/main.py" || ! -f "$REPO_ROOT/crazy_functional.py" || ! -f "$REPO_ROOT/core_functional.py" ]]; then
  echo "--repo-root must point to a GPT Academic checkout containing main.py." >&2
  exit 2
fi

cd "$REPO_ROOT"
"${PYTHON_BIN}" - <<'PYCODE'
import sys
try:
    import gradio
    version = getattr(gradio, "__version__", "unknown")
    if version != "3.32.15":
        raise RuntimeError(f"Expected gradio 3.32.15, found {version}. Run: python -m pip install -r requirements.txt")
    import toolbox, core_functional, crazy_functional  # noqa: F401
except ModuleNotFoundError as exc:
    if exc.name == "pkg_resources":
        print("Missing pkg_resources for gradio 3.32.15. Run: python -m pip install 'setuptools<81'", file=sys.stderr)
    else:
        print(f"Missing module {exc.name}. Run: python -m pip install -r requirements.txt", file=sys.stderr)
    raise
print("GPT Academic import preflight passed.")
PYCODE

exec "${PYTHON_BIN}" main.py "${ARGS[@]}"
