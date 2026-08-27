#!/usr/bin/env python3
"""Safe MobileNet forward smoke test for 3DDFA.

This script adapts the repo's CPU speed smoke into a single deterministic shape
check. It intentionally does not import the native inference CLI, dlib, render
utilities, or checkpoints.
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


KNOWN_ARCHES = ("mobilenet_2", "mobilenet_1", "mobilenet_075", "mobilenet_05", "mobilenet_025")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one safe 3DDFA MobileNet forward pass and validate output shape."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to a 3DDFA checkout containing mobilenet_v1.py (default: current directory).",
    )
    parser.add_argument(
        "--arch",
        default="mobilenet_1",
        choices=KNOWN_ARCHES,
        help="MobileNet constructor to instantiate (default: mobilenet_1).",
    )
    parser.add_argument(
        "--num-classes",
        type=int,
        default=62,
        help="Output dimension for the MobileNet head (default: 62).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Synthetic batch size for the smoke input (default: 1).",
    )
    parser.add_argument(
        "--input-size",
        type=int,
        default=120,
        help="Synthetic square input size; native inference uses 120 (default: 120).",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cpu",
        help="Requested forward device. CUDA falls back to CPU unless --strict-device is set.",
    )
    parser.add_argument(
        "--strict-device",
        action="store_true",
        help="Fail instead of falling back when --device cuda is requested but unavailable.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.batch_size <= 0:
        print("ERROR: --batch-size must be positive", file=sys.stderr)
        return 2
    if args.input_size <= 0:
        print("ERROR: --input-size must be positive", file=sys.stderr)
        return 2
    if args.num_classes <= 0:
        print("ERROR: --num-classes must be positive", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_root).expanduser().resolve()
    mobilenet_file = repo_root / "mobilenet_v1.py"
    if not mobilenet_file.is_file():
        print(f"ERROR: missing mobilenet_v1.py under repo root: {repo_root}", file=sys.stderr)
        return 1

    sys.path.insert(0, str(repo_root))

    try:
        torch = importlib.import_module("torch")
    except Exception as exc:  # pragma: no cover - depends on caller environment
        print(f"ERROR: cannot import torch: {exc}", file=sys.stderr)
        return 1

    try:
        mobilenet_v1 = importlib.import_module("mobilenet_v1")
    except Exception as exc:
        print(f"ERROR: cannot import mobilenet_v1 from repo root: {exc}", file=sys.stderr)
        return 1

    ctor = getattr(mobilenet_v1, args.arch, None)
    if ctor is None:
        print(f"ERROR: architecture {args.arch!r} is not defined", file=sys.stderr)
        return 1

    device = "cpu"
    if args.device == "cuda":
        if torch.cuda.is_available():
            device = "cuda"
        elif args.strict_device:
            print("ERROR: CUDA requested but torch.cuda.is_available() is false", file=sys.stderr)
            return 1
        else:
            print("WARN: CUDA requested but unavailable; falling back to CPU for smoke only.")
            print("WARN: This does not verify native GPU inference.")

    try:
        model = ctor(num_classes=args.num_classes)
        model.eval()
        model.to(device)
        data = torch.rand(args.batch_size, 3, args.input_size, args.input_size, device=device)
        with torch.no_grad():
            output = model(data)
    except Exception as exc:
        print(f"ERROR: forward smoke failed: {exc}", file=sys.stderr)
        return 1

    actual_shape = tuple(output.shape)
    expected_shape = (args.batch_size, args.num_classes)
    if actual_shape != expected_shape:
        print(
            f"ERROR: unexpected output shape {actual_shape}; expected {expected_shape}",
            file=sys.stderr,
        )
        return 1

    print(
        "OK: {arch}(num_classes={classes}) forward produced shape {shape} on {device}".format(
            arch=args.arch,
            classes=args.num_classes,
            shape=actual_shape,
            device=device,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
