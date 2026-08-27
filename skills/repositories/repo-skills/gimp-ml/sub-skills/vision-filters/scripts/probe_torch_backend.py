#!/usr/bin/env python3
"""Report Torch CPU/CUDA state without allocating a large tensor."""

from __future__ import annotations

import argparse
import platform
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Probe installed PyTorch CPU/CUDA availability and device names. "
            "The probe does not allocate tensors, load weights, use the network, "
            "or change the host."
        )
    )
    parser.add_argument(
        "--cuda-index",
        type=int,
        default=None,
        help="optionally inspect one CUDA device index (default: all visible devices)",
    )
    return parser


def safe_call(label: str, fn: Any) -> bool:
    try:
        value = fn()
    except Exception as exc:  # backend probes must report, not hide, host errors
        print(f"{label}: ERROR {type(exc).__name__}: {exc}")
        return False
    print(f"{label}: {value}")
    return True


def main() -> int:
    args = build_parser().parse_args()
    print(f"python: {sys.version.split()[0]}")
    print(f"platform: {platform.platform()}")
    try:
        import torch
    except Exception as exc:
        print(f"torch import: ERROR {type(exc).__name__}: {exc}")
        print("recommendation: use Force CPU only after a compatible Torch install is available")
        return 2

    print(f"torch: {getattr(torch, '__version__', 'unknown')}")
    print(f"cpu available: True (Torch imported; device={torch.device('cpu')})")
    cuda_ok = safe_call("cuda available", torch.cuda.is_available)
    if not cuda_ok:
        print("recommendation: select Force CPU and investigate the backend error")
        return 1

    try:
        count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    except Exception as exc:
        print(f"cuda device count: ERROR {type(exc).__name__}: {exc}")
        print("recommendation: select Force CPU; CUDA device enumeration failed")
        return 1
    print(f"cuda device count: {count}")

    if not torch.cuda.is_available() or count == 0:
        print("recommendation: select Force CPU; no CUDA device is available")
        return 0

    indices = [args.cuda_index] if args.cuda_index is not None else list(range(count))
    had_error = False
    for index in indices:
        if index < 0 or index >= count:
            print(f"cuda:{index}: ERROR index outside visible device range 0..{count - 1}")
            had_error = True
            continue
        try:
            name = torch.cuda.get_device_name(index)
            capability = torch.cuda.get_device_capability(index)
        except Exception as exc:
            print(f"cuda:{index}: ERROR {type(exc).__name__}: {exc}")
            had_error = True
            continue
        print(f"cuda:{index} name: {name}")
        print(f"cuda:{index} capability: {capability[0]}.{capability[1]}")

    print("allocation test: skipped (this probe intentionally performs no tensor allocation)")
    if had_error:
        print("recommendation: select Force CPU until CUDA enumeration errors are resolved")
        return 1
    print("recommendation: CUDA is visible, but availability does not prove model-memory capacity; Force CPU remains valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
