#!/usr/bin/env python3
"""Inspect the installed EasyOCR runtime without downloading model weights."""

from __future__ import annotations

import argparse
import inspect
import json
from importlib.metadata import version


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect the EasyOCR install and backend readiness.")
    parser.add_argument("--lang", default="en", help="Language code to pass to Reader for the smoke init.")
    parser.add_argument(
        "--gpu",
        default="auto",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Backend hint for the smoke init.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a compact JSON summary instead of human-readable text.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    import easyocr  # local import so --help stays cheap
    import torch

    gpu_arg: bool | str
    if args.gpu == "auto":
        gpu_arg = True
    elif args.gpu == "cpu":
        gpu_arg = False
    else:
        gpu_arg = args.gpu

    reader = easyocr.Reader(
        [args.lang],
        gpu=gpu_arg,
        detector=False,
        recognizer=False,
        download_enabled=False,
        verbose=False,
    )

    summary = {
        "easyocr_version": version("easyocr"),
        "module": easyocr.__file__,
        "reader_signature": str(inspect.signature(easyocr.Reader)),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "mps_available": bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()),
        "reader_device": reader.device,
        "reader_quantize_type": type(reader.quantize).__name__,
        "reader_quantize_value": repr(reader.quantize),
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        for key, value in summary.items():
            print(f"{key}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
