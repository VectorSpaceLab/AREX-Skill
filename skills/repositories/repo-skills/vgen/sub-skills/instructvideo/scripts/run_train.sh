#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run_train.sh [--repo-root PATH] [--config PATH] [--dry-run] [--] [extra args...]

Forward the InstructVideo reward-fine-tuning config to the repo's train_net.py
entrypoint.
EOF
}

REPO_ROOT="."
CONFIG="configs/instructvideo/train/reward_webvid_ani45_20_reg_vidldm_LoRA_TSNExp16Diffreward_Partial06_Trunc1_Check_ddim20.yaml"
DRY_RUN=0
EXTRA=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$2"
      shift 2
      ;;
    --config)
      CONFIG="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      EXTRA+=("$@")
      break
      ;;
    *)
      EXTRA+=("$1")
      shift
      ;;
  esac
done

if [[ ! -f "$REPO_ROOT/train_net.py" ]]; then
  echo "ERROR: train_net.py was not found under '$REPO_ROOT'. Point --repo-root at a VGen checkout." >&2
  exit 1
fi

if [[ -f "$CONFIG" ]]; then
  CONFIG_PATH="$CONFIG"
elif [[ -f "$REPO_ROOT/$CONFIG" ]]; then
  CONFIG_PATH="$REPO_ROOT/$CONFIG"
else
  echo "ERROR: config file not found: $CONFIG" >&2
  exit 1
fi

cmd=(python "$REPO_ROOT/train_net.py" --cfg "$CONFIG_PATH")
if [[ ${#EXTRA[@]} -gt 0 ]]; then
  cmd+=("${EXTRA[@]}")
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf 'Would run:'
  printf ' %q' "${cmd[@]}"
  printf '\n'
  exit 0
fi

exec "${cmd[@]}"
