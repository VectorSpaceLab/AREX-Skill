#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  else
    echo "error: no python interpreter found in PATH" >&2
    exit 1
  fi
fi

echo "== Python =="
"${PYTHON_BIN}" -I - <<'PY'
mods = [
    "torch",
    "transformers",
    "datasets",
    "vllm",
    "deepspeed",
    "colossalai",
    "openai",
    "tree_sitter",
    "tree_sitter_c",
    "editdistance",
    "pandas",
    "loguru",
]
for mod_name in mods:
    try:
        mod = __import__(mod_name)
        print(f"{mod_name}: ok ({getattr(mod, '__file__', 'built-in')})")
    except Exception as exc:
        print(f"{mod_name}: FAIL ({exc})")
PY

echo
for bin_name in gcc g++ objdump java clang-format; do
  if command -v "${bin_name}" >/dev/null 2>&1; then
    echo "== ${bin_name} =="
    "${bin_name}" --version | head -n 1
  else
    echo "== ${bin_name} =="
    echo "not found"
  fi
done

if "${PYTHON_BIN}" - <<'PY'
try:
    import torch
    print(torch.__version__)
    print(torch.version.cuda)
    print(torch.cuda.is_available())
    print(torch.cuda.device_count())
except Exception:
    raise SystemExit(1)
PY
then
  echo "CUDA smoke: torch import succeeded"
fi
