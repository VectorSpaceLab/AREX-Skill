#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
REPO_ROOT="$PWD"
PYTHON="${PYTHON:-python}"
RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$(cd "$2" && pwd)"
      shift 2
      ;;
    --run)
      RUN=1
      shift
      ;;
    --help|-h)
      cat <<'EOF'
Usage: run_train_checked.sh [--repo-root PATH] [--run]

Validate the AnyDoor environment and then print or run:
  $PYTHON run_train_anydoor.py

Set PYTHON to the prepared interpreter if you do not want to rely on the
current shell lookup.
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

"$PYTHON" "$SKILL_ROOT/scripts/check_anydoor_environment.py" --repo-root "$REPO_ROOT"
"$PYTHON" "$SCRIPT_DIR/check_dataset_config.py" --config "$REPO_ROOT/configs/datasets.yaml" || true

if [[ "$RUN" -eq 1 ]]; then
  cd "$REPO_ROOT"
  "$PYTHON" run_train_anydoor.py
else
  echo "dry-run: cd \"$REPO_ROOT\" && $PYTHON run_train_anydoor.py"
fi
