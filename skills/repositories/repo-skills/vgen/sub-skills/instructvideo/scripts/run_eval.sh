#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run_eval.sh [--repo-root PATH] [--preset NAME|--config PATH] [--dry-run] [--list-presets] [--] [extra args...]

Forward an InstructVideo evaluation config to the repo's inference.py entrypoint.
The bundled presets use the actual config filenames present in the VGen repo.
EOF
}

list_presets() {
  cat <<'EOF'
lora-ddim50-in-domain
lora-ddim20-in-domain
lora-ddim20-new-animals
lora-ddim20-non-animals
base-ddim20-in-domain
base-ddim20-new-animals
base-ddim20-non-animals
EOF
}

preset_to_config() {
  case "$1" in
    lora-ddim50-in-domain)
      echo "configs/instructvideo/eval/instructvideo_infer_UNetSD_t2v_webvid_LoRA_webvid_ddim50_in-domain.yaml"
      ;;
    lora-ddim20-in-domain)
      echo "configs/instructvideo/eval/instructvideo_infer_UNetSD_t2v_webvid_LoRA_webvid_ddim20_in-domain.yaml"
      ;;
    lora-ddim20-new-animals)
      echo "configs/instructvideo/eval/instructvideo_infer_UNetSD_t2v_webvid_LoRA_ddim20_generalization_new-animals.yaml"
      ;;
    lora-ddim20-non-animals)
      echo "configs/instructvideo/eval/instructvideo_infer_UNetSD_t2v_webvid_LoRA_ddim20_generalization_non-animals.yaml"
      ;;
    base-ddim20-in-domain)
      echo "configs/instructvideo/eval/modelscopet2v_infer_UNetSD_t2v_ddim20_in-domain.yaml"
      ;;
    base-ddim20-new-animals)
      echo "configs/instructvideo/eval/modelscopet2v_infer_UNetSD_t2v_ddim20_new-animals.yaml"
      ;;
    base-ddim20-non-animals)
      echo "configs/instructvideo/eval/modelscopet2v_infer_UNetSD_t2v_ddim20_non-animals.yaml"
      ;;
    *)
      return 1
      ;;
  esac
}

REPO_ROOT="."
PRESET="lora-ddim50-in-domain"
CONFIG=""
DRY_RUN=0
EXTRA=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$2"
      shift 2
      ;;
    --preset)
      PRESET="$2"
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
    --list-presets)
      list_presets
      exit 0
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

if [[ ! -f "$REPO_ROOT/inference.py" ]]; then
  echo "ERROR: inference.py was not found under '$REPO_ROOT'. Point --repo-root at a VGen checkout." >&2
  exit 1
fi

if [[ -z "$CONFIG" ]]; then
  if ! CONFIG="$(preset_to_config "$PRESET")"; then
    echo "ERROR: unknown preset '$PRESET'. Use --list-presets." >&2
    exit 1
  fi
fi

if [[ -f "$CONFIG" ]]; then
  CONFIG_PATH="$CONFIG"
elif [[ -f "$REPO_ROOT/$CONFIG" ]]; then
  CONFIG_PATH="$REPO_ROOT/$CONFIG"
else
  echo "ERROR: config file not found: $CONFIG" >&2
  exit 1
fi

cmd=(python "$REPO_ROOT/inference.py" --cfg "$CONFIG_PATH")
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
