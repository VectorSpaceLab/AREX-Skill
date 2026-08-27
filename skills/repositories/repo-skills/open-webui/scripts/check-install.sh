#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"
OPEN_WEBUI_BIN="${OPEN_WEBUI_BIN:-}"
CHECK_CUDA="${CHECK_CUDA:-0}"

if [[ -z "$OPEN_WEBUI_BIN" ]]; then
  if command -v open-webui >/dev/null 2>&1; then
    OPEN_WEBUI_BIN="$(command -v open-webui)"
  else
    OPEN_WEBUI_BIN="$(cd "$(dirname "$PYTHON_BIN")" && pwd)/open-webui"
  fi
fi

say() {
  printf '\n==> %s\n' "$1"
}

say "Python identity"
"$PYTHON_BIN" -I -c 'import sys; print(sys.executable); print(sys.version)'

say "Installed distribution version"
"$PYTHON_BIN" -I -c 'from importlib.metadata import version; print(version("open-webui"))'

say "Package import"
"$PYTHON_BIN" -I -c 'import open_webui; print(open_webui.__file__)'

say "CLI help"
"$OPEN_WEBUI_BIN" --help
"$OPEN_WEBUI_BIN" serve --help
"$OPEN_WEBUI_BIN" dev --help

if [[ "$CHECK_CUDA" == "1" ]]; then
  say "CUDA smoke"
  "$PYTHON_BIN" - <<'PY'
import torch
print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.is_available())
print(torch.cuda.device_count())
if torch.cuda.is_available() and torch.cuda.device_count():
    print(torch.cuda.get_device_name(0))
    print(torch.cuda.get_device_capability(0))
    x = torch.empty((1,), device='cuda')
    print(x)
PY
fi
