#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${IMAGE_TAG:-main}"
PORT="${PORT:-3000}"
NAME="${NAME:-open-webui}"
DATA_VOLUME="${DATA_VOLUME:-open-webui}"
OLLAMA_VOLUME="${OLLAMA_VOLUME:-ollama}"
DRY_RUN="${DRY_RUN:-0}"

case "$IMAGE_TAG" in
  main|cuda|cuda126|ollama|slim) ;;
  *)
    echo "Unsupported IMAGE_TAG: $IMAGE_TAG" >&2
    echo "Use one of: main, cuda, cuda126, ollama, slim" >&2
    exit 1
    ;;
esac

IMAGE="${IMAGE:-ghcr.io/open-webui/open-webui:${IMAGE_TAG}}"

cmd=(docker run -d -p "${PORT}:8080" --add-host=host.docker.internal:host-gateway -v "${DATA_VOLUME}:/app/backend/data" --name "$NAME" --restart always)

if [[ "$IMAGE_TAG" == "cuda" || "$IMAGE_TAG" == "cuda126" || "${USE_CUDA:-0}" == "1" ]]; then
  cmd+=(--gpus all)
fi

if [[ "$IMAGE_TAG" == "ollama" || "${BUNDLE_OLLAMA:-0}" == "1" ]]; then
  cmd+=(-v "${OLLAMA_VOLUME}:/root/.ollama")
fi

for var in OLLAMA_BASE_URL OPENAI_API_KEY ANTHROPIC_API_KEY GOOGLE_API_KEY WEBUI_SECRET_KEY WEBUI_JWT_SECRET_KEY; do
  if [[ -n "${!var:-}" ]]; then
    cmd+=(-e "${var}=${!var}")
  fi
done

if [[ "$DRY_RUN" == "1" ]]; then
  printf '%q ' "${cmd[@]}" "$IMAGE"
  printf '\n'
  exit 0
fi

exec "${cmd[@]}" "$IMAGE"
