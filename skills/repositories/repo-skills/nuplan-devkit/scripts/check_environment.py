#!/usr/bin/env python3
"""Read-only nuPlan package and optional backend smoke check.

This helper does not inspect or modify a dataset, start a service, create
experiment files, download weights, or run training. It is useful after
installing a route-specific dependency set.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import sys
from typing import List


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cuda", action="store_true", help="also require a usable CUDA Torch device")
    args = parser.parse_args()

    failures: List[str] = []
    try:
        version = importlib.metadata.version("nuplan-devkit")
        print(f"PASS distribution nuplan-devkit {version}")
    except importlib.metadata.PackageNotFoundError:
        failures.append("nuplan-devkit distribution metadata is missing")

    try:
        package = importlib.import_module("nuplan")
        print(f"PASS import nuplan ({package.__file__})")
    except Exception as exc:  # pragma: no cover - environment dependent
        failures.append(f"nuplan import failed: {type(exc).__name__}: {exc}")

    try:
        cli = importlib.import_module("nuplan.cli.nuplan_cli")
        print(f"PASS import CLI module ({cli.__name__})")
    except Exception as exc:  # pragma: no cover - environment dependent
        failures.append(f"CLI import failed: {type(exc).__name__}: {exc}")

    try:
        import torch

        print(f"PASS torch {torch.__version__} (CUDA {torch.version.cuda})")
        if args.cuda:
            if not torch.cuda.is_available():
                failures.append("CUDA was requested but torch.cuda.is_available() is false")
            else:
                device = torch.device("cuda")
                probe = torch.zeros((1,), device=device)
                print(f"PASS CUDA device {torch.cuda.get_device_name(0)} ({probe.device})")
    except ImportError:
        if args.cuda:
            failures.append("CUDA was requested but PyTorch is not installed")
        else:
            print("INFO PyTorch is not installed; Torch/model routes remain unavailable")
    except Exception as exc:  # pragma: no cover - environment dependent
        failures.append(f"Torch smoke failed: {type(exc).__name__}: {exc}")

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    print("All requested environment checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
