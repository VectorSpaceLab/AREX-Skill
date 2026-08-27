#!/usr/bin/env bash
set -euo pipefail

say() { printf '%s\n' "$*"; }

say "DeepStream-Yolo toolchain probe"
say "PWD: $(pwd)"
say "Kernel: $(uname -srmo 2>/dev/null || uname -a)"
say "CUDA_VER: ${CUDA_VER:-<unset>}"
say ""

for cmd in nvidia-smi nvcc deepstream-app pkg-config make g++ python3.11 python3 conda uv; do
  if command -v "$cmd" >/dev/null 2>&1; then
    say "FOUND $cmd: $(command -v "$cmd")"
  else
    say "MISSING $cmd"
  fi
done

say ""
if command -v nvidia-smi >/dev/null 2>&1; then
  say "nvidia-smi -L"
  nvidia-smi -L || true
fi

if command -v pkg-config >/dev/null 2>&1; then
  say ""
  say "pkg-config glib-2.0: $(pkg-config --modversion glib-2.0 2>/dev/null || echo missing)"
  say "pkg-config opencv4: $(pkg-config --modversion opencv4 2>/dev/null || echo missing)"
fi

if command -v deepstream-app >/dev/null 2>&1; then
  say ""
  say "deepstream-app --version-all"
  deepstream-app --version-all || true
fi

say ""
say "Probe complete. Missing DeepStream / CUDA toolkit entries mean the runtime build path is not ready yet."
