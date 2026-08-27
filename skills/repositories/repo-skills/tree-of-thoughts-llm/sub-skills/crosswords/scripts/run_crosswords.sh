#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-bfs}"
if [[ $# -gt 0 ]]; then
  shift
fi

case "${MODE}" in
  bfs)
    exec python "${SCRIPT_DIR}/../../../scripts/run_tot.py"           --task crosswords           --task_start_index 0           --task_end_index 20           --method_generate sample           --method_evaluate vote           --method_select greedy           --n_generate_sample 10           --n_evaluate_sample 1           --n_select_sample 1           --prompt_sample cot           "$@"
    ;;
  standard)
    exec python "${SCRIPT_DIR}/../../../scripts/run_tot.py"           --task crosswords           --task_start_index 0           --task_end_index 20           --naive_run           --prompt_sample standard           --n_generate_sample 10           "$@"
    ;;
  cot)
    exec python "${SCRIPT_DIR}/../../../scripts/run_tot.py"           --task crosswords           --task_start_index 0           --task_end_index 20           --naive_run           --prompt_sample cot           --n_generate_sample 10           "$@"
    ;;
  dfs)
    exec python "${SCRIPT_DIR}/dfs_search.py" "$@"
    ;;
  *)
    cat >&2 <<'EOF'
Usage: run_crosswords.sh {bfs|standard|cot|dfs} [additional args]
EOF
    exit 2
    ;;
esac
