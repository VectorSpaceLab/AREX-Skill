#!/usr/bin/env python3
"""Safely diagnose a NeuroMANCER installation and optional backends.

Usage:
  python scripts/check_environment.py --help
  python scripts/check_environment.py --run

The helper performs read-only imports and tiny CPU/CUDA probes. It does not
install packages, download data, train a model, or write files.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import sys


MODULES = (
    "neuromancer",
    "neuromancer.constraint",
    "neuromancer.loss",
    "neuromancer.problem",
    "neuromancer.system",
    "neuromancer.dataset",
    "neuromancer.trainer",
    "neuromancer.dynamics",
    "neuromancer.modules",
    "neuromancer.psl",
    "neuromancer.slim",
)
OPTIONAL = ("torchdiffeq", "torchsde", "lightning", "cvxpy", "cvxpylayers", "casadi", "requests")


def run() -> int:
    try:
        version = importlib.metadata.version("neuromancer")
    except importlib.metadata.PackageNotFoundError:
        print("FAIL: neuromancer distribution is not installed", file=sys.stderr)
        return 2
    print(f"neuromancer distribution: {version}")
    failures = []
    for name in MODULES:
        try:
            importlib.import_module(name)
            print(f"PASS import: {name}")
        except Exception as exc:  # diagnostic output should name the failing route
            failures.append(name)
            print(f"FAIL import: {name}: {type(exc).__name__}: {exc}")
    for name in OPTIONAL:
        try:
            module = importlib.import_module(name)
            version_text = getattr(module, "__version__", "available")
            print(f"OPTIONAL {name}: {version_text}")
        except Exception as exc:
            print(f"OPTIONAL {name}: unavailable ({type(exc).__name__}: {exc})")
    try:
        import torch

        print(f"torch: {torch.__version__}; cuda_build={torch.version.cuda}")
        print(f"cpu smoke: {torch.ones(2).sum().item():.1f}")
        if torch.cuda.is_available():
            try:
                device = torch.device("cuda")
                value = torch.ones(1, device=device)
                print(f"cuda smoke: passed on {torch.cuda.get_device_name(0)} ({value.item():.1f})")
            except Exception as exc:
                print(f"cuda smoke: unverified ({type(exc).__name__}: {exc})")
        else:
            print("cuda smoke: not available (optional)")
    except Exception as exc:
        failures.append("torch")
        print(f"FAIL torch smoke: {type(exc).__name__}: {exc}")
    if failures:
        print("required import failures: " + ", ".join(failures), file=sys.stderr)
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="run read-only package and backend checks")
    args = parser.parse_args()
    if args.run:
        raise SystemExit(run())
    parser.print_help()


if __name__ == "__main__":
    main()
