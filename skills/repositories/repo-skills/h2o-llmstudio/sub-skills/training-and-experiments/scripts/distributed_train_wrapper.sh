#!/usr/bin/env bash
# Build a validated H2O LLM Studio distributed training command.
# Safe by default: prints the command and exits unless --execute is provided.
# Example dry run:
#   ./distributed_train_wrapper.sh --num-gpus 2 --yaml cfg.yaml
# Example execute:
#   ./distributed_train_wrapper.sh --num-gpus 2 --cuda-visible-devices 0,1 --yaml cfg.yaml --execute

set -euo pipefail

show_help() {
  cat <<'HELP'
Usage: distributed_train_wrapper.sh --num-gpus N --yaml CFG [options] [-- TRAIN_ARGS...]

Build or execute a multi-GPU H2O LLM Studio training command.
Dry-run is the default. Add --execute to run.

Required:
  --num-gpus N                 Number of processes/GPUs to launch. Must be >= 1.
  --yaml CFG                   YAML config path passed to llm_studio/train.py -Y.

Options:
  --launcher torchrun|deepspeed  Launcher to use. Default: torchrun.
  --cuda-visible-devices LIST    Optional CUDA_VISIBLE_DEVICES value, e.g. 0,1.
  --master-port PORT             Optional master port for torchrun/deepspeed.
  --python PYTHON                Python executable used to locate llm_studio/train.py. Default: python.
  --train-script PATH            Explicit path to train.py; otherwise resolved from installed llm_studio.
  --execute                      Actually run the command. Without this, only print it.
  -h, --help                     Show this help.
  --                             Remaining args are appended after -Y CFG.

Examples:
  distributed_train_wrapper.sh --num-gpus 2 --yaml cfg.yaml
  distributed_train_wrapper.sh --num-gpus 4 --cuda-visible-devices 0,1,2,3 --yaml cfg.yaml -- --training.epochs 1
  distributed_train_wrapper.sh --launcher deepspeed --num-gpus 2 --yaml cfg.yaml --execute

Notes:
  - This wrapper does not validate YAML semantics or train a model in dry-run mode.
  - DeepSpeed requires an installed deepspeed executable and a valid CUDA toolkit/nvcc setup.
HELP
}

launcher="torchrun"
num_gpus=""
yaml_path=""
cuda_visible=""
master_port=""
python_bin="python"
train_script=""
execute=0
extra_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --launcher)
      launcher="${2:-}"; shift 2 ;;
    --num-gpus)
      num_gpus="${2:-}"; shift 2 ;;
    --yaml|-Y)
      yaml_path="${2:-}"; shift 2 ;;
    --cuda-visible-devices)
      cuda_visible="${2:-}"; shift 2 ;;
    --master-port)
      master_port="${2:-}"; shift 2 ;;
    --python)
      python_bin="${2:-}"; shift 2 ;;
    --train-script)
      train_script="${2:-}"; shift 2 ;;
    --execute)
      execute=1; shift ;;
    -h|--help)
      show_help; exit 0 ;;
    --)
      shift; extra_args+=("$@"); break ;;
    *)
      echo "error: unknown argument: $1" >&2
      echo "Use --help for usage." >&2
      exit 2 ;;
  esac
done

if [[ -z "$num_gpus" || ! "$num_gpus" =~ ^[0-9]+$ || "$num_gpus" -lt 1 ]]; then
  echo "error: --num-gpus must be an integer >= 1" >&2
  exit 2
fi
if [[ -z "$yaml_path" ]]; then
  echo "error: --yaml CFG is required" >&2
  exit 2
fi
if [[ ! -f "$yaml_path" ]]; then
  echo "error: YAML config not found: $yaml_path" >&2
  exit 2
fi
if [[ "$launcher" != "torchrun" && "$launcher" != "deepspeed" ]]; then
  echo "error: --launcher must be torchrun or deepspeed" >&2
  exit 2
fi
if [[ "$launcher" == "deepspeed" && "$num_gpus" -lt 2 ]]; then
  echo "error: H2O LLM Studio config checks require at least two GPUs for DeepSpeed" >&2
  exit 2
fi
if [[ -n "$master_port" && ! "$master_port" =~ ^[0-9]+$ ]]; then
  echo "error: --master-port must be numeric" >&2
  exit 2
fi
if ! command -v "$python_bin" >/dev/null 2>&1; then
  echo "error: python executable not found: $python_bin" >&2
  exit 2
fi

if [[ -z "$train_script" ]]; then
  train_script="$($python_bin - <<'PY'
import importlib.util
import pathlib
import sys
spec = importlib.util.find_spec("llm_studio")
if spec is None or spec.origin is None:
    sys.exit("could not import/locate llm_studio; pass --train-script explicitly")
print(pathlib.Path(spec.origin).with_name("train.py"))
PY
)" || {
    echo "error: could not resolve llm_studio/train.py; pass --train-script explicitly" >&2
    exit 2
  }
fi
if [[ ! -f "$train_script" ]]; then
  echo "error: train script not found: $train_script" >&2
  exit 2
fi

cmd=()
if [[ "$launcher" == "torchrun" ]]; then
  if command -v torchrun >/dev/null 2>&1; then
    cmd+=("torchrun" "--nproc_per_node=$num_gpus")
  else
    cmd+=("$python_bin" "-m" "torch.distributed.run" "--nproc_per_node=$num_gpus")
  fi
  if [[ -n "$master_port" ]]; then
    cmd+=("--master_port=$master_port")
  fi
  cmd+=("$train_script" "-Y" "$yaml_path")
else
  if ! command -v deepspeed >/dev/null 2>&1; then
    echo "error: deepspeed executable not found on PATH" >&2
    exit 2
  fi
  include_devices="$cuda_visible"
  if [[ -z "$include_devices" ]]; then
    include_devices="$(seq -s, 0 $((num_gpus - 1)))"
  fi
  cmd+=("deepspeed" "--include" "localhost:${include_devices}")
  if [[ -n "$master_port" ]]; then
    cmd+=("--master_port" "$master_port")
  fi
  cmd+=("$train_script" "-Y" "$yaml_path")
fi
cmd+=("${extra_args[@]}")

if [[ -n "$cuda_visible" && "$launcher" == "torchrun" ]]; then
  echo "CUDA_VISIBLE_DEVICES=$cuda_visible ${cmd[*]}"
else
  printf '%q ' "${cmd[@]}"
  echo
fi

if [[ "$execute" -ne 1 ]]; then
  echo "dry-run only; add --execute to run" >&2
  exit 0
fi

if [[ -n "$cuda_visible" && "$launcher" == "torchrun" ]]; then
  CUDA_VISIBLE_DEVICES="$cuda_visible" "${cmd[@]}"
else
  "${cmd[@]}"
fi
