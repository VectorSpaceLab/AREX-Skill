#!/usr/bin/env python3
"""Safe import and backend smoke for CVNets.

Run this from anywhere with `--repo-root /path/to/ml-cvnets` to verify that the
checkout imports, that the top-level repo modules resolve, and that the current
machine can execute a small CPU and optional CUDA tensor smoke.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from importlib.metadata import PackageNotFoundError

from _bootstrap import activate_repo_root

REQUIRED_IMPORTS = [
    "cvnets",
    "data",
    "engine",
    "loss_fn",
    "metrics",
    "optim",
    "options",
    "utils",
    "main_train",
    "main_eval",
    "main_conversion",
    "main_benchmark",
    "main_loss_landscape",
]

OPTIONAL_IMPORTS = [
    "torchvision",
    "torchaudio",
    "torchtext",
    "av",
    "fvcore",
    "coremltools",
    "pycocotools",
    "ftfy",
]


def import_status(name: str) -> tuple[bool, str | None]:
    try:
        importlib.import_module(name)
        return True, None
    except Exception as exc:  # pragma: no cover - exercised by runtime environments
        return False, f"{exc.__class__.__name__}: {exc}"


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except PackageNotFoundError:
        return "<not-installed>"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to a CVNets checkout.",
    )
    parser.add_argument(
        "--strict-optional",
        action="store_true",
        help="Return a non-zero exit code when optional extras are missing.",
    )
    args = parser.parse_args(argv)

    repo_root = activate_repo_root(args.repo_root)

    results: dict[str, object] = {
        "repo_root": repo_root.name,
        "cvnets_version": package_version("cvnets"),
        "required": {},
        "optional": {},
    }

    required_failures: list[str] = []
    optional_failures: list[str] = []

    for name in REQUIRED_IMPORTS:
        ok, err = import_status(name)
        results["required"][name] = "ok" if ok else err
        if not ok:
            required_failures.append(f"{name}: {err}")

    for name in OPTIONAL_IMPORTS:
        ok, err = import_status(name)
        results["optional"][name] = "ok" if ok else err
        if not ok:
            optional_failures.append(f"{name}: {err}")

    import torch

    cpu_smoke = float(torch.randn(2, 3).sum())
    cuda_summary: dict[str, object]
    if torch.cuda.is_available():
        cuda_value = float(torch.tensor([2.0], device="cuda").sum())
        cuda_summary = {
            "available": True,
            "count": torch.cuda.device_count(),
            "device0": torch.cuda.get_device_name(0),
            "tensor_smoke": cuda_value,
        }
    else:
        cuda_summary = {"available": False, "count": 0, "device0": None}

    results["cpu_smoke"] = cpu_smoke
    results["cuda"] = cuda_summary

    print(json.dumps(results, indent=2, sort_keys=True))

    if required_failures:
        print("\nRequired imports failed:", file=sys.stderr)
        for item in required_failures:
            print(f"- {item}", file=sys.stderr)
        return 1

    if args.strict_optional and optional_failures:
        print("\nOptional imports missing:", file=sys.stderr)
        for item in optional_failures:
            print(f"- {item}", file=sys.stderr)
        return 2

    if optional_failures:
        print("\nOptional imports missing (non-fatal):", file=sys.stderr)
        for item in optional_failures:
            print(f"- {item}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
