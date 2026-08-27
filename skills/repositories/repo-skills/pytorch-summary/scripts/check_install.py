#!/usr/bin/env python3
"""Check a runtime for the legacy torchsummary package.

This helper is safe by default: it imports torchsummary, torch, and numpy,
prints public signatures/backend facts, and optionally runs a tiny CPU/CUDA
summary smoke test. It does not download data or depend on the source checkout.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from typing import Sequence, Tuple


def as_int(value: object) -> int:
    """Convert Python ints and scalar tensors to plain int."""

    if hasattr(value, "item"):
        return int(value.item())  # type: ignore[union-attr]
    return int(value)  # type: ignore[arg-type]


def normalize_counts(counts: Sequence[object]) -> Tuple[int, int]:
    if len(counts) != 2:
        raise AssertionError(f"expected two parameter counts, received {counts!r}")
    return as_int(counts[0]), as_int(counts[1])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify torchsummary import/signature/device basics with a tiny model.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="device for the tiny summary smoke test (default: cpu)",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="only print import, version, signature, and backend facts",
    )
    args = parser.parse_args()

    try:
        import numpy
        import torch
        import torchsummary
        from torchsummary import summary_string
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown"
        print(
            f"[fail] missing import {missing!r}. Install torchsummary plus its "
            "runtime dependencies torch and numpy in this Python environment.",
            file=sys.stderr,
        )
        return 2

    print(f"python: {sys.version.split()[0]}")
    print(f"torchsummary module: {torchsummary.__file__}")
    print(f"torch: {torch.__version__}")
    print(f"numpy: {numpy.__version__}")
    print(f"summary signature: {inspect.signature(torchsummary.summary)}")
    print(f"summary_string signature: {inspect.signature(torchsummary.summary_string)}")
    print(f"torch cuda version: {torch.version.cuda}")
    print(f"torch cuda available: {torch.cuda.is_available()}")
    print(f"torch cuda device count: {torch.cuda.device_count()}")

    if args.skip_smoke:
        return 0

    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        print(
            f"[fail] requested {device}, but torch.cuda.is_available() is false",
            file=sys.stderr,
        )
        return 3

    model = torch.nn.Linear(2, 5).to(device)
    text, counts = summary_string(model, (1, 2), device=device)
    total, trainable = normalize_counts(counts)
    if (total, trainable) != (15, 15):
        print(
            f"[fail] tiny Linear expected counts (15, 15), observed {(total, trainable)}",
            file=sys.stderr,
        )
        return 4
    if "Linear" not in text or "Total params" not in text:
        print("[fail] summary_string output did not include expected table markers", file=sys.stderr)
        return 5

    print(f"[ok] tiny Linear summary on {device}: total_params={total} trainable_params={trainable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
