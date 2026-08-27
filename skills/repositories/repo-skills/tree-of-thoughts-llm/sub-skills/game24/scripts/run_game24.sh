#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-bfs}"
if [[ $# -gt 0 ]]; then
  shift
fi

case "${MODE}" in
  bfs)
    exec python "${SCRIPT_DIR}/../../../scripts/run_tot.py"           --task game24           --task_start_index 900           --task_end_index 1000           --method_generate propose           --method_evaluate value           --method_select greedy           --n_evaluate_sample 3           --n_select_sample 5           "$@"
    ;;
  standard)
    exec python "${SCRIPT_DIR}/../../../scripts/run_tot.py"           --task game24           --task_start_index 900           --task_end_index 1000           --naive_run           --prompt_sample standard           --n_generate_sample 100           "$@"
    ;;
  cot)
    exec python "${SCRIPT_DIR}/../../../scripts/run_tot.py"           --task game24           --task_start_index 900           --task_end_index 1000           --naive_run           --prompt_sample cot           --n_generate_sample 100           "$@"
    ;;
  *)
    cat >&2 <<'EOF'
Usage: run_game24.sh {bfs|standard|cot} [additional run_tot.py args]
EOF
    exit 2
    ;;
esac
