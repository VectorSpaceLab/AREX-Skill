#!/usr/bin/env bash
# Run the CULane evaluator with explicit paths.
#
# Purpose: safer replacement for the repo's run-full.sh and run-lite.sh snippets.
#
# Example:
#   ./run_culane_evaluator.sh --repo-root . --data-root <CULANE_ROOT> \
#     --detect-root <DETECTION_LINES_DIR> --output-root <SCORES_DIR> --mode full

set -euo pipefail

repo_root=""
data_root=""
detect_root=""
output_root=""
mode="full"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root) repo_root="$2"; shift 2 ;;
    --data-root) data_root="$2"; shift 2 ;;
    --detect-root) detect_root="$2"; shift 2 ;;
    --output-root) output_root="$2"; shift 2 ;;
    --mode) mode="$2"; shift 2 ;;
    -h|--help)
      cat <<'EOF'
Usage: run_culane_evaluator.sh --repo-root PATH --data-root PATH --detect-root PATH --output-root PATH [--mode full|lite]
EOF
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

: "${repo_root:?set --repo-root}"
: "${data_root:?set --data-root}"
: "${detect_root:?set --detect-root}"
: "${output_root:?set --output-root}"

if [[ -x "${repo_root}/evaluation/culane/evaluate" ]]; then
  eval_bin="${repo_root}/evaluation/culane/evaluate"
elif [[ -x "${repo_root}/evaluation/culane/build/culane_evaluator" ]]; then
  eval_bin="${repo_root}/evaluation/culane/build/culane_evaluator"
else
  echo "missing CULane evaluator binary under ${repo_root}/evaluation/culane" >&2
  exit 3
fi

mkdir -p "${output_root}"

run_one() {
  local list_file="$1"
  local out_file="$2"
  "${eval_bin}" -a "${data_root}" -d "${detect_root}" -i "${data_root}" -l "${list_file}" -w 30 -t 0.5 -c 1640 -r 590 -f 1 -o "${out_file}"
}

if [[ "${mode}" == "lite" ]]; then
  run_one "${data_root}/list/test.txt" "${output_root}/lite.txt"
else
  run_one "${data_root}/list/test_split/test0_normal.txt" "${output_root}/out0_normal.txt"
  run_one "${data_root}/list/test_split/test1_crowd.txt" "${output_root}/out1_crowd.txt"
  run_one "${data_root}/list/test_split/test2_hlight.txt" "${output_root}/out2_hlight.txt"
  run_one "${data_root}/list/test_split/test3_shadow.txt" "${output_root}/out3_shadow.txt"
  run_one "${data_root}/list/test_split/test4_noline.txt" "${output_root}/out4_noline.txt"
  run_one "${data_root}/list/test_split/test5_arrow.txt" "${output_root}/out5_arrow.txt"
  run_one "${data_root}/list/test_split/test6_curve.txt" "${output_root}/out6_curve.txt"
  run_one "${data_root}/list/test_split/test7_cross.txt" "${output_root}/out7_cross.txt"
  run_one "${data_root}/list/test_split/test8_night.txt" "${output_root}/out8_night.txt"
fi

echo "CULane evaluator finished in ${output_root}"
