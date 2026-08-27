#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVAL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -f "${EVAL_ROOT}/config.env" ]]; then
  set -a
  source "${EVAL_ROOT}/config.env"
  set +a
fi

BENCH_REPO_ROOT="${BENCH_REPO_ROOT:?Set BENCH_REPO_ROOT in config.env or environment}"
OBJDUMP_BIN="${OBJDUMP:-objdump}"
NUM_JOBS="${JOBS:-}"

if ! command -v "${OBJDUMP_BIN}" >/dev/null 2>&1; then
  echo "error: objdump binary '${OBJDUMP_BIN}' not found" >&2
  exit 1
fi

if [[ -z "${NUM_JOBS}" ]]; then
  if command -v nproc >/dev/null 2>&1; then
    NUM_JOBS="$(nproc)"
  elif [[ "$(uname)" == "Darwin" ]]; then
    NUM_JOBS="$(sysctl -n hw.ncpu)"
  else
    NUM_JOBS=4
  fi
fi

if ! [[ "${NUM_JOBS}" =~ ^[0-9]+$ ]] || (( NUM_JOBS <= 0 )); then
  echo "error: invalid JOBS value '${NUM_JOBS}'" >&2
  exit 1
fi

readarray -t BINARIES < <(
  find "${BENCH_REPO_ROOT}" -mindepth 2 -maxdepth 2 -type f \
    \( -iname '*.o0' -o -iname '*.o1' -o -iname '*.o2' -o -iname '*.o3' \) \
    ! -path "${BENCH_REPO_ROOT}/scripts/*" \
    ! -path "${BENCH_REPO_ROOT}/target/*" \
    ! -path "${BENCH_REPO_ROOT}/common/*" \
    ! -path "${BENCH_REPO_ROOT}/.git/*" \
    | sort
)

if [[ ${#BINARIES[@]} -eq 0 ]]; then
  echo "error: no O0/O1/O2/O3 binaries found under ${BENCH_REPO_ROOT}" >&2
  exit 1
fi

export OBJDUMP_BIN BENCH_REPO_ROOT

printf '%s\0' "${BINARIES[@]}" | xargs -0 -n1 -P "${NUM_JOBS}" bash -c '
  binary_path="$1"
  bench_repo_root="${BENCH_REPO_ROOT}"
  output_path="${binary_path}.s"
  rel_in="${binary_path#"${bench_repo_root}/"}"
  rel_out="${output_path#"${bench_repo_root}/"}"
  echo "==> Disassembling ${rel_in} -> ${rel_out}"
  "${OBJDUMP_BIN}" -d "${binary_path}" > "${output_path}"
' _

echo "Assembly listings written alongside each binary (extension .s)."
