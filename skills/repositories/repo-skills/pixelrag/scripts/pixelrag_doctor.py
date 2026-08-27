#!/usr/bin/env python3
"""Read-only PixelRAG environment diagnostic.

Checks imports, console scripts, optional modules, Chrome discovery, and CUDA
availability without downloading models, rendering pages, starting services, or
building indexes.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys


def check_import(name: str) -> bool:
    try:
        mod = importlib.import_module(name)
        print(f"ok import {name}: {getattr(mod, '__file__', '<namespace>')}")
        return True
    except Exception as exc:
        print(f"FAIL import {name}: {exc}")
        return False


def check_cmd(cmd: str) -> bool:
    path = shutil.which(cmd)
    if not path:
        print(f"FAIL command {cmd}: not on PATH")
        return False
    print(f"ok command {cmd}: {path}")
    try:
        r = subprocess.run([path, "--help"], text=True, capture_output=True, timeout=20)
        print(f"  --help exit={r.returncode}")
        return r.returncode == 0
    except Exception as exc:
        print(f"  FAIL --help: {exc}")
        return False


def check_chrome() -> bool:
    path = shutil.which("pixelshot")
    if not path:
        return False
    try:
        r = subprocess.run([path, "which-chrome"], text=True, capture_output=True, timeout=30)
        if r.returncode == 0:
            print(f"ok chrome: {r.stdout.strip()}")
            return True
        print(f"WARN chrome: {r.stderr.strip() or r.stdout.strip()}")
        return False
    except Exception as exc:
        print(f"WARN chrome check failed: {exc}")
        return False


def check_cuda() -> bool:
    try:
        import torch
    except Exception as exc:
        print(f"WARN torch unavailable: {exc}")
        return False
    print(f"torch {torch.__version__} cuda_runtime={getattr(torch.version, 'cuda', None)} available={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"cuda devices={torch.cuda.device_count()} first={torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-cuda", action="store_true")
    args = parser.parse_args()

    ok = True
    for name in ["pixelrag", "pixelrag_render"]:
        ok = check_import(name) and ok
    for name in ["pixelrag_embed", "pixelrag_index", "pixelrag_serve"]:
        check_import(name)
    for cmd in ["pixelshot", "pixelrag"]:
        ok = check_cmd(cmd) and ok
    check_chrome()
    if not args.skip_cuda:
        check_cuda()
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
