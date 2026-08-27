#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OPEN_WEBUI_BIN="${OPEN_WEBUI_BIN:-}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"
RELOAD="${RELOAD:-1}"
CORS_ALLOW_ORIGIN="${CORS_ALLOW_ORIGIN:-http://localhost:5173;http://localhost:8080}"

if [[ -z "$OPEN_WEBUI_BIN" ]]; then
  if command -v open-webui >/dev/null 2>&1; then
    OPEN_WEBUI_BIN="$(command -v open-webui)"
  else
    OPEN_WEBUI_BIN="$(cd "$(dirname "$PYTHON_BIN")" && pwd)/open-webui"
  fi
fi

if [[ -z "${WEBUI_SECRET_KEY:-}" && -z "${WEBUI_JWT_SECRET_KEY:-}" ]]; then
  export WEBUI_SECRET_KEY
  WEBUI_SECRET_KEY="$($PYTHON_BIN - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)"
fi

export CORS_ALLOW_ORIGIN

reload_args=()
if [[ "$RELOAD" == "0" || "${RELOAD,,}" == "false" ]]; then
  reload_args+=(--no-reload)
else
  reload_args+=(--reload)
fi

exec "$OPEN_WEBUI_BIN" dev --host "$HOST" --port "$PORT" "${reload_args[@]}"
