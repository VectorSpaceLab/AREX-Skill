#!/usr/bin/env python3
"""Read-only control/physics/CATK prerequisite probe.

This helper reports import and path facts only. It does not install packages,
launch services, download models, read credentials, or run inference.
"""
from __future__ import annotations

import argparse
import importlib
from pathlib import Path
import sys


MODULES = (
    "alpasim_controller",
    "alpasim_physics",
    "warp",
    "torch",
    "torch_geometric",
    "torch_cluster",
    "alpasim_trafficsim.grpc.config",
    "alpasim_trafficsim.grpc.servicer",
)


def check_module(name: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # imports can fail with backend-specific errors
        return False, f"{type(exc).__name__}: {exc}"
    return True, str(getattr(module, "__file__", "imported"))


def check_path(label: str, value: str | None, *, suffix: str | None = None) -> None:
    if value is None:
        return
    path = Path(value).expanduser()
    if suffix is None:
        state = "exists" if path.exists() else "MISSING"
    elif path.is_dir():
        matches = sorted(path.rglob(f"*{suffix}"))
        state = f"exists ({len(matches)} matching files)" if matches else f"exists (no {suffix} files)"
    else:
        state = "MISSING"
    print(f"path {label}: {path} [{state}]")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usdz-folder", help="Existing scene directory to inspect")
    parser.add_argument("--model-config", help="Existing CATK config file to inspect")
    parser.add_argument("--checkpoint", help="Existing CATK checkpoint to inspect")
    parser.add_argument("--token-dir", help="Existing CATK token directory to inspect")
    args = parser.parse_args(argv)

    print(f"python: {sys.executable}")
    print(f"version: {sys.version.split()[0]}")
    for name in MODULES:
        ok, detail = check_module(name)
        print(f"import {name}: {'OK' if ok else 'BLOCKED'} ({detail})")

    try:
        import torch
    except Exception:
        pass
    else:
        try:
            print(f"torch.cuda.is_available: {torch.cuda.is_available()}")
            print(f"torch.version.cuda: {torch.version.cuda}")
        except Exception as exc:
            print(f"torch CUDA probe: {type(exc).__name__}: {exc}")

    check_path("usdz-folder", args.usdz_folder, suffix=".usdz")
    check_path("model-config", args.model_config)
    check_path("checkpoint", args.checkpoint)
    check_path("token-dir", args.token_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
