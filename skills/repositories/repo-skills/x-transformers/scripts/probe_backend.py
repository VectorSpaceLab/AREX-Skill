#!/usr/bin/env python3
"""Probe the local x-transformers backend and optional flash-attn support.

This helper is intentionally read-only. It reports the package version, torch
version, CUDA availability, and whether flash_attn is importable.
"""

from __future__ import annotations

import argparse
import json
from importlib import metadata, util
from typing import Any


def collect() -> dict[str, Any]:
    import torch

    try:
        x_version = metadata.version("x-transformers")
    except metadata.PackageNotFoundError:
        x_version = None

    info: dict[str, Any] = {
        "x_transformers_version": x_version,
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
        "flash_attn_present": util.find_spec("flash_attn") is not None,
    }

    if info["cuda_available"] and torch.cuda.device_count() > 0:
        info["cuda_device_name"] = torch.cuda.get_device_name(0)
        info["cuda_device_capability"] = list(torch.cuda.get_device_capability(0))
    else:
        info["cuda_device_name"] = None
        info["cuda_device_capability"] = None

    return info


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe x-transformers runtime backend support.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    info = collect()
    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
        return

    print(f"x-transformers: {info['x_transformers_version']}")
    print(f"torch: {info['torch_version']} (cuda={info['torch_cuda_version']})")
    print(f"cuda_available: {info['cuda_available']}")
    print(f"cuda_device_count: {info['cuda_device_count']}")
    print(f"cuda_device_name: {info['cuda_device_name']}")
    print(f"cuda_device_capability: {info['cuda_device_capability']}")
    print(f"flash_attn_present: {info['flash_attn_present']}")


if __name__ == "__main__":
    main()
