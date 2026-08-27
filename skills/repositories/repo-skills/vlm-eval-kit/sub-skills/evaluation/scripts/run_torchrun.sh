#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_torchrun.sh [options] -- <run.py arguments>

Safe wrapper for launching VLMEvalKit with torchrun across visible GPUs.
Run it from a VLMEvalKit working tree, or pass --run-py PATH.

Options:
  --gpus N          Use N processes instead of auto-detecting visible GPUs.
  --run-py PATH     Path to run.py (default: run.py in the current directory).
  --torchrun PATH   torchrun executable (default: torchrun from PATH).
  --dry-run         Print the command without executing it.
  -h, --help        Show this help.

Examples:
  ./run_torchrun.sh --dry-run -- --data MME --model qwen_chat --work-dir outputs
  CUDA_VISIBLE_DEVICES=0,1 ./run_torchrun.sh -- --data MME --model qwen_chat
EOF
}

run_py="${RUN_PY:-run.py}"
torchrun_bin="${TORCHRUN:-torchrun}"
dry_run=0
requested_gpus=""
args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --gpus)
      [[ $# -ge 2 ]] || { echo "error: --gpus requires a value" >&2; exit 2; }
      requested_gpus="$2"
      shift 2
      ;;
    --run-py)
      [[ $# -ge 2 ]] || { echo "error: --run-py requires a value" >&2; exit 2; }
      run_py="$2"
      shift 2
      ;;
    --torchrun)
      [[ $# -ge 2 ]] || { echo "error: --torchrun requires a value" >&2; exit 2; }
      torchrun_bin="$2"
      shift 2
      ;;
    --)
      shift
      args+=("$@")
      break
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

if [[ ${#args[@]} -eq 0 ]]; then
  echo "error: no run.py arguments supplied" >&2
  usage >&2
  exit 2
fi

if ! [[ "$requested_gpus" =~ ^[1-9][0-9]*$|^$ ]]; then
  echo "error: --gpus must be a positive integer" >&2
  exit 2
fi

if [[ ! -f "$run_py" ]]; then
  echo "error: run.py not found at '$run_py'. Run from a VLMEvalKit tree or pass --run-py." >&2
  exit 2
fi

if ! command -v "$torchrun_bin" >/dev/null 2>&1; then
  echo "error: torchrun executable '$torchrun_bin' not found in PATH" >&2
  exit 2
fi

count_visible_gpus() {
  if [[ -n "$requested_gpus" ]]; then
    printf '%s\n' "$requested_gpus"
    return
  fi

  if [[ -n "${CUDA_VISIBLE_DEVICES:-}" && "${CUDA_VISIBLE_DEVICES}" != "-1" ]]; then
    python - <<'PY'
import os
items = [x.strip() for x in os.environ.get('CUDA_VISIBLE_DEVICES', '').split(',')]
items = [x for x in items if x and x.lower() not in {'none', 'nodevfiles'}]
print(len(items))
PY
    return
  fi

  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --list-gpus 2>/dev/null | sed '/^$/d' | wc -l | tr -d ' '
    return
  fi

  printf '0\n'
}

gpus="$(count_visible_gpus)"
if ! [[ "$gpus" =~ ^[0-9]+$ ]]; then
  echo "error: could not determine visible GPU count" >&2
  exit 2
fi

if [[ "$gpus" -lt 1 ]]; then
  cat >&2 <<'EOF'
error: no visible GPUs detected for torchrun.
Use plain `python run.py ...` for CPU/API-only workflows, or set CUDA_VISIBLE_DEVICES / --gpus after confirming GPU availability.
EOF
  exit 2
fi

cmd=("$torchrun_bin" "--nproc-per-node=$gpus" "$run_py" "${args[@]}")

printf 'VLMEvalKit torchrun command (%s GPU process%s):\n' "$gpus" "$([[ "$gpus" == 1 ]] && echo '' || echo 'es')"
printf '  '
printf '%q ' "${cmd[@]}"
printf '\n'

if [[ "$dry_run" -eq 1 ]]; then
  exit 0
fi

exec "${cmd[@]}"
