#!/usr/bin/env bash
# Preview or execute a small sequence of Lightning-Hydra-Template training commands.
# This is a safe adaptation of the repo's scripts/schedule.sh: dry-run is the default.
# Example:
#   bash run_scheduled_training.sh --repo-root . --max-epochs 5 10 --logger csv
#   bash run_scheduled_training.sh --repo-root . --max-epochs 1 --extra debug=fdr --execute

set -euo pipefail

REPO_ROOT="."
PYTHON_BIN="python"
LOGGER="csv"
EXECUTE=0
EXTRA_ARGS=()
MAX_EPOCHS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$2"; shift 2 ;;
    --python)
      PYTHON_BIN="$2"; shift 2 ;;
    --logger)
      LOGGER="$2"; shift 2 ;;
    --max-epochs)
      shift
      while [[ $# -gt 0 && "$1" != --* ]]; do MAX_EPOCHS+=("$1"); shift; done ;;
    --extra)
      EXTRA_ARGS+=("$2"); shift 2 ;;
    --execute)
      EXECUTE=1; shift ;;
    --help|-h)
      sed -n '1,40p' "$0"; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ ${#MAX_EPOCHS[@]} -eq 0 ]]; then
  MAX_EPOCHS=(5 10)
fi

cd "$REPO_ROOT"
if [[ ! -f "src/train.py" ]]; then
  echo "src/train.py not found under $REPO_ROOT" >&2
  exit 2
fi

for epochs in "${MAX_EPOCHS[@]}"; do
  cmd=("$PYTHON_BIN" "src/train.py" "trainer.max_epochs=$epochs" "logger=$LOGGER" "${EXTRA_ARGS[@]}")
  printf 'Command:'
  printf ' %q' "${cmd[@]}"
  printf '\n'
  if [[ "$EXECUTE" -eq 1 ]]; then
    "${cmd[@]}"
  fi
done

if [[ "$EXECUTE" -ne 1 ]]; then
  echo "Dry-run only. Re-run with --execute to launch training."
fi
