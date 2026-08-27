#!/usr/bin/env bash
# Safely evaluate every TaskBench prediction JSON in a user-provided checkout.
# No network calls are made by this wrapper; native evaluate.py may write metrics
# under DATA_DIR according to TaskBench's own save-dir logic.
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: batch_evaluate.sh REPO_ROOT DATA_DIR PREDICTION_DIR [PYTHON]

Arguments:
  REPO_ROOT       Checkout containing taskbench/evaluate.py.
  DATA_DIR        TaskBench data directory containing data.json.
  PREDICTION_DIR  Prediction directory name relative to DATA_DIR.
  PYTHON          Python executable to use; defaults to python.
EOF
}

if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  usage
  exit 2
fi

REPO_ROOT=$1
DATA_DIR=$2
PREDICTION_DIR=$3
PYTHON=${4:-python}

EVALUATE_PY="$REPO_ROOT/taskbench/evaluate.py"
PREDICTION_PATH="$DATA_DIR/$PREDICTION_DIR"

if [ ! -f "$EVALUATE_PY" ]; then
  echo "error: expected TaskBench evaluator at: $EVALUATE_PY" >&2
  exit 2
fi

if [ ! -d "$DATA_DIR" ]; then
  echo "error: DATA_DIR does not exist or is not a directory: $DATA_DIR" >&2
  exit 2
fi

if [ ! -d "$PREDICTION_PATH" ]; then
  echo "error: prediction directory does not exist: $PREDICTION_PATH" >&2
  exit 2
fi

set -- "$PREDICTION_PATH"/*.json
if [ ! -e "$1" ]; then
  echo "error: no prediction .json files found in: $PREDICTION_PATH" >&2
  exit 2
fi

DATA_BASENAME=$(basename -- "$DATA_DIR" | tr '[:upper:]' '[:lower:]')
case "$DATA_BASENAME" in
  *dailylifeapis*) DEPENDENCY_TYPE=temporal ;;
  *) DEPENDENCY_TYPE=resource ;;
esac

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "error: Python executable not found: $PYTHON" >&2
  exit 2
fi

echo "TaskBench batch evaluation"
echo "  repo root:       $REPO_ROOT"
echo "  data dir:        $DATA_DIR"
echo "  prediction dir:  $PREDICTION_DIR"
echo "  dependency type: $DEPENDENCY_TYPE"
echo "  python:          $PYTHON"

for prediction_file in "$PREDICTION_PATH"/*.json; do
  [ -f "$prediction_file" ] || continue
  prediction_name=${prediction_file##*/}
  llm=${prediction_name%.json}
  echo "Evaluating '$llm' from '$PREDICTION_DIR/$prediction_name'..."
  "$PYTHON" "$EVALUATE_PY" \
    --data_dir "$DATA_DIR" \
    --prediction_dir "$PREDICTION_DIR" \
    --llm "$llm" \
    --splits all \
    --n_tools all \
    --mode add \
    --dependency_type "$DEPENDENCY_TYPE" \
    -m all
  echo "Finished '$llm'."
done

echo "TaskBench batch evaluation complete."
