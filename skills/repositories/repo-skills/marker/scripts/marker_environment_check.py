#!/usr/bin/env python3
"""Safe Marker environment probe.

This script checks package metadata, imports, torch backend facts, and optional
console-script help. It does not convert documents, start servers, download
models, launch apps, or call external APIs.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import shutil
import subprocess
import sys
from pathlib import Path


def dist_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "missing"


def check_import(module: str) -> bool:
    try:
        importlib.import_module(module)
    except Exception as exc:  # pragma: no cover - diagnostic script
        print(f"IMPORT {module}: FAIL {exc.__class__.__name__}: {exc}")
        return False
    print(f"IMPORT {module}: OK")
    return True


def find_executable(command: str) -> str | None:
    exe = shutil.which(command)
    if exe:
        return exe
    sibling = Path(sys.executable).resolve().parent / command
    if sibling.exists() and sibling.is_file():
        return str(sibling)
    return None


def check_cli(command: str, timeout: int) -> bool:
    exe = find_executable(command)
    if not exe:
        print(f"CLI {command}: missing on PATH and next to the active Python")
        return False
    try:
        result = subprocess.run(
            [exe, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - diagnostic script
        print(f"CLI {command}: FAIL {exc.__class__.__name__}: {exc}")
        return False
    first = (result.stdout or "").splitlines()[0] if result.stdout else ""
    status = "OK" if result.returncode == 0 else f"exit {result.returncode}"
    print(f"CLI {command}: {status} {first}")
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a Marker installation without running conversion.")
    parser.add_argument("--check-cli", action="store_true", help="Run --help for Marker console scripts.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout per CLI help command.")
    args = parser.parse_args()

    print(f"python: {sys.version.split()[0]}")
    for dist in ["marker-pdf", "torch", "surya-ocr", "pdftext", "transformers"]:
        print(f"DIST {dist}: {dist_version(dist)}")

    ok = True
    for module in ["marker", "marker.config.parser", "marker.converters.pdf", "marker.output"]:
        ok = check_import(module) and ok

    try:
        import torch

        print(f"TORCH version: {torch.__version__}")
        print(f"TORCH cuda: {getattr(torch.version, 'cuda', None)} available={torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"TORCH cuda devices: {torch.cuda.device_count()}")
    except Exception as exc:  # pragma: no cover - diagnostic script
        ok = False
        print(f"TORCH check: FAIL {exc.__class__.__name__}: {exc}")

    if args.check_cli:
        for command in ["marker_single", "marker", "marker_chunk_convert", "marker_server"]:
            ok = check_cli(command, args.timeout) and ok

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
