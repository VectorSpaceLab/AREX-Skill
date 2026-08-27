#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-bfs}"
if [[ $# -gt 0 ]]; then
  shift
fi

case "${MODE}" in
  bfs)
    exec python "${SCRIPT_DIR}/../../../scripts/run_tot.py"           --task text           --task_start_index 0           --task_end_index 100           --method_generate sample           --method_evaluate vote           --method_select greedy           --n_generate_sample 5           --n_evaluate_sample 5           --n_select_sample 1           --prompt_sample cot           --temperature 1.0           "$@"
    ;;
  standard)
    exec python "${SCRIPT_DIR}/../../../scripts/run_tot.py"           --task text           --task_start_index 0           --task_end_index 100           --naive_run           --prompt_sample standard           --n_generate_sample 10           --temperature 1.0           "$@"
    ;;
  cot)
    exec python "${SCRIPT_DIR}/../../../scripts/run_tot.py"           --task text           --task_start_index 0           --task_end_index 100           --naive_run           --prompt_sample cot           --n_generate_sample 10           --temperature 1.0           "$@"
    ;;
  *)
    cat >&2 <<'EOF'
Usage: run_text.sh {bfs|standard|cot} [additional run_tot.py args]
EOF
    exit 2
    ;;
esac
