#!/usr/bin/env python3
"""Safe Pytorch-UNet model API smoke check.

Imports UNet from the active Python environment, runs a tiny forward pass, checks
that output shape matches (batch, classes, height, width), and prints JSON.
CPU is the default. CUDA is optional and can be required with --require-cuda.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict


def _emit(payload: Dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(exit_code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe Pytorch-UNet forward-pass smoke check")
    parser.add_argument("--channels", type=int, default=3, help="Input tensor channels / UNet n_channels")
    parser.add_argument("--classes", type=int, default=2, help="Output classes / UNet n_classes")
    parser.add_argument("--height", type=int, default=32, help="Input tensor height")
    parser.add_argument("--width", type=int, default=32, help="Input tensor width")
    parser.add_argument("--batch", type=int, default=1, help="Input batch size")
    parser.add_argument("--bilinear", action="store_true", help="Use bilinear upsampling instead of transposed conv")
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="cpu",
        help="Execution device. Default is CPU for portable functional checks.",
    )
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA is unavailable")
    parser.add_argument("--amp", action="store_true", help="Use torch.autocast for the forward pass when supported")
    parser.add_argument("--seed", type=int, default=0, help="Manual torch seed for deterministic input generation")
    parser.add_argument(
        "--repo-root",
        help="Optional Pytorch-UNet checkout root to add to sys.path before importing unet.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.channels <= 0 or args.classes <= 0 or args.batch <= 0:
        _emit(
            {
                "ok": False,
                "error": "channels, classes, and batch must be positive integers",
                "args": vars(args),
            },
            2,
        )
    if args.height < 16 or args.width < 16:
        _emit(
            {
                "ok": False,
                "error": "height and width must be at least 16 because UNet downsamples four times",
                "args": vars(args),
            },
            2,
        )

    # When executed as a file from this skill's scripts/ directory, Python puts
    # the script directory on sys.path instead of the caller's checkout root.
    # Adding the current working directory lets agents run this smoke check from
    # an importable checkout without hard-coding any local path.
    if args.repo_root:
        repo_root = os.path.abspath(args.repo_root)
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
    cwd = os.getcwd()
    if cwd and cwd not in sys.path:
        sys.path.insert(0, cwd)

    try:
        import torch
        from unet import UNet
    except Exception as exc:  # pragma: no cover - environment-dependent diagnostic
        _emit(
            {
                "ok": False,
                "stage": "import",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "hint": "Run from an environment where Pytorch-UNet is installed, or run from a checkout root that contains the unet package.",
            },
            1,
        )

    cuda_available = bool(torch.cuda.is_available())
    if args.require_cuda and not cuda_available:
        _emit(
            {
                "ok": False,
                "stage": "device",
                "error": "CUDA was required but torch.cuda.is_available() is false",
                "cuda_available": cuda_available,
                "torch_version": torch.__version__,
            },
            1,
        )

    if args.require_cuda:
        device_name = "cuda"
    elif args.device == "auto":
        device_name = "cuda" if cuda_available else "cpu"
    else:
        device_name = args.device

    if device_name == "cuda" and not cuda_available:
        _emit(
            {
                "ok": False,
                "stage": "device",
                "error": "CUDA device requested but torch.cuda.is_available() is false",
                "cuda_available": cuda_available,
                "torch_version": torch.__version__,
            },
            1,
        )

    device = torch.device(device_name)
    expected_shape = (args.batch, args.classes, args.height, args.width)

    try:
        torch.manual_seed(args.seed)
        net = UNet(n_channels=args.channels, n_classes=args.classes, bilinear=args.bilinear)
        net.eval()
        net.to(device=device)
        x = torch.randn(args.batch, args.channels, args.height, args.width, device=device)

        start = time.perf_counter()
        autocast_device = device.type if device.type != "mps" else "cpu"
        use_amp = bool(args.amp)
        with torch.inference_mode(), torch.autocast(autocast_device, enabled=use_amp):
            y = net(x)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        actual_shape = tuple(int(dim) for dim in y.shape)
        if actual_shape != expected_shape:
            _emit(
                {
                    "ok": False,
                    "stage": "forward",
                    "error": "unexpected output shape",
                    "expected_shape": list(expected_shape),
                    "actual_shape": list(actual_shape),
                    "device": str(device),
                    "torch_version": torch.__version__,
                },
                1,
            )

        _emit(
            {
                "ok": True,
                "model": "UNet",
                "n_channels": args.channels,
                "n_classes": args.classes,
                "bilinear": bool(args.bilinear),
                "input_shape": [args.batch, args.channels, args.height, args.width],
                "output_shape": list(actual_shape),
                "device": str(device),
                "cuda_available": cuda_available,
                "amp": use_amp,
                "torch_version": torch.__version__,
                "elapsed_ms": round(elapsed_ms, 3),
            },
            0,
        )
    except Exception as exc:  # pragma: no cover - runtime diagnostic path
        _emit(
            {
                "ok": False,
                "stage": "forward",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "expected_shape": list(expected_shape),
                "device": str(device),
                "torch_version": torch.__version__,
            },
            1,
        )


if __name__ == "__main__":
    main()
