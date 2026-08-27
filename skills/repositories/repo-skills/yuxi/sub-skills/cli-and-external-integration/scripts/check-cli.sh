#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
REMOTE_URL=""
LIVE_PING=false

usage() {
  cat <<'EOF'
Usage: check-cli.sh [--python-bin PYTHON] [--remote-url URL]

Offline by default. It checks CLI help registration and config loading.
Pass --remote-url to opt into one live remote ping inside a temporary HOME.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python-bin)
      [[ $# -ge 2 ]] || { echo "--python-bin needs a value" >&2; exit 2; }
      PYTHON_BIN="$2"
      shift 2
      ;;
    --remote-url)
      [[ $# -ge 2 ]] || { echo "--remote-url needs a value" >&2; exit 2; }
      REMOTE_URL="$2"
      LIVE_PING=true
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python binary not found: $PYTHON_BIN" >&2
  exit 127
fi

run_cli() {
  "$PYTHON_BIN" -m yuxi_cli "$@"
}

echo "[offline] yuxi --version"
run_cli --version >/dev/null

echo "[offline] yuxi --help"
run_cli --help >/dev/null

echo "[offline] yuxi login --help"
run_cli login --help >/dev/null

echo "[offline] yuxi chat --help"
run_cli chat --help >/dev/null

echo "[offline] yuxi remote --help"
run_cli remote --help >/dev/null

echo "[offline] yuxi kb --help"
run_cli kb --help >/dev/null

echo "[offline] yuxi kb upload --help"
run_cli kb upload --help >/dev/null

echo "[offline] yuxi agent eval --help"
run_cli agent eval --help >/dev/null

echo "[offline] config load"
"$PYTHON_BIN" - <<'PY'
from yuxi_cli.config import ConfigStore

config = ConfigStore().load()
remote = config.get_remote()
print(f"current={config.current} remote={remote.name} url={remote.url}")
PY

if [[ "$LIVE_PING" == true ]]; then
  tmp_home="$(mktemp -d)"
  trap 'rm -rf "$tmp_home"' EXIT

  echo "[live] remote ping: $REMOTE_URL"
  HOME="$tmp_home" "$PYTHON_BIN" -m yuxi_cli remote add smoke "$REMOTE_URL" >/dev/null
  HOME="$tmp_home" "$PYTHON_BIN" -m yuxi_cli remote use smoke >/dev/null
  HOME="$tmp_home" "$PYTHON_BIN" -m yuxi_cli remote ping smoke
else
  echo "[live] skipped (pass --remote-url to opt in)"
fi
