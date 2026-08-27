#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: launch_eval.sh [options] [-- extra DAMO-YOLO config opts]

Self-contained launcher for DAMO-YOLO COCO evaluation using the bundled
eval_entrypoint.py and an installed `damo` package. It does not call repo-local
tools/eval.py.

Required:
  --config PATH          DAMO-YOLO Python config file
  --ckpt PATH            Local PyTorch checkpoint for evaluation

Common options:
  --workdir PATH         Directory used to resolve relative paths inside config
  --gpus N               Number of visible GPUs to use (default: 1)
  --master-port PORT     Distributed master port (default: 29502)
  --fuse                 Fuse conv/bn before evaluation
  --python PATH          Python executable (default: python)
  --dry-run              Print final command without running it
  -h, --help             Show this help

Pass-through compatibility options:
  --conf VALUE --nms VALUE --tsize INT --seed INT --test

Anything after -- is appended to eval_entrypoint.py as raw trailing opts.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG=""
CKPT=""
WORKDIR=""
NPROC="${NPROC_PER_NODE:-${GPUS:-1}}"
MASTER_PORT="${MASTER_PORT:-29502}"
PYTHON="${PYTHON:-python}"
FUSE=0
TEST=0
CONF=""
NMS=""
TSIZE=""
SEED=""
DRY_RUN=0
EXTRA_ARGS=()

while (($#)); do
  case "$1" in
    --config|-f) CONFIG="$2"; shift 2 ;;
    --ckpt|-c) CKPT="$2"; shift 2 ;;
    --workdir) WORKDIR="$2"; shift 2 ;;
    --gpus|--nproc-per-node|--nproc_per_node) NPROC="$2"; shift 2 ;;
    --master-port) MASTER_PORT="$2"; shift 2 ;;
    --conf) CONF="$2"; shift 2 ;;
    --nms) NMS="$2"; shift 2 ;;
    --tsize) TSIZE="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --fuse) FUSE=1; shift ;;
    --test) TEST=1; shift ;;
    --python) PYTHON="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; EXTRA_ARGS=("$@"); break ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$CONFIG" ]]; then
  echo "ERROR: --config is required" >&2
  exit 2
fi
if [[ -z "$CKPT" ]]; then
  echo "ERROR: --ckpt is required" >&2
  exit 2
fi
if [[ ! -f "$CONFIG" ]]; then
  echo "ERROR: config file not found: $CONFIG" >&2
  exit 1
fi
if [[ ! -f "$CKPT" ]]; then
  echo "ERROR: checkpoint not found: $CKPT" >&2
  exit 1
fi
if ! [[ "$NPROC" =~ ^[0-9]+$ ]] || (( NPROC < 1 )); then
  echo "ERROR: --gpus/--nproc_per_node must be a positive integer" >&2
  exit 2
fi

validator=("$PYTHON" "$SCRIPT_DIR/validate_coco_config.py" --config "$CONFIG" --split val --check-images 0)
if [[ -n "$WORKDIR" ]]; then
  validator+=(--workdir "$WORKDIR")
fi
"${validator[@]}"

"$PYTHON" - "$NPROC" <<'PY'
import sys
import torch
nproc = int(sys.argv[1])
if not torch.cuda.is_available():
    print("ERROR: torch.cuda.is_available() is false; DAMO-YOLO evaluation requires CUDA.")
    raise SystemExit(1)
visible = torch.cuda.device_count()
if visible < nproc:
    print(f"ERROR: only {visible} CUDA device(s) are visible but requested {nproc}.")
    raise SystemExit(1)
if not torch.distributed.is_nccl_available():
    print("ERROR: torch.distributed.is_nccl_available() is false; DAMO-YOLO launchers use NCCL.")
    raise SystemExit(1)
print(f"CUDA/NCCL preflight OK: visible_gpus={visible}; requested={nproc}")
PY

cmd=(
  "$PYTHON" -m torch.distributed.run
  --nproc_per_node "$NPROC"
  --master_port "$MASTER_PORT"
  "$SCRIPT_DIR/eval_entrypoint.py"
  -f "$CONFIG"
  -c "$CKPT"
)
if [[ -n "$WORKDIR" ]]; then
  cmd+=(--workdir "$WORKDIR")
fi
if [[ -n "$CONF" ]]; then cmd+=(--conf "$CONF"); fi
if [[ -n "$NMS" ]]; then cmd+=(--nms "$NMS"); fi
if [[ -n "$TSIZE" ]]; then cmd+=(--tsize "$TSIZE"); fi
if [[ -n "$SEED" ]]; then cmd+=(--seed "$SEED"); fi
if (( FUSE )); then cmd+=(--fuse); fi
if (( TEST )); then cmd+=(--test); fi
if ((${#EXTRA_ARGS[@]})); then cmd+=("${EXTRA_ARGS[@]}"); fi

if (( DRY_RUN )); then
  printf 'Command: '
  printf '%q ' "${cmd[@]}"
  printf '\n'
  exit 0
fi

exec "${cmd[@]}"
