#!/usr/bin/env python3
"""Report CUDA, cuDNN, and CTranslate2 readiness without blocking for input."""

from __future__ import annotations

import argparse
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when CUDA is absent. By default, absent CUDA is reported as CPU-only readiness.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        import torch
        from torch.backends import cudnn
    except Exception as exc:
        print(f"[cuda] torch import failed: {exc.__class__.__name__}: {exc}")
        return 1

    print(f"[cuda] torch={torch.__version__}")
    print(f"[cuda] torch.version.cuda={torch.version.cuda}")

    cuda_available = torch.cuda.is_available()
    print(f"[cuda] torch.cuda.is_available()={cuda_available}")
    if not cuda_available:
        print("[cuda] CUDA is unavailable; keep devtype=cpu unless the host backend is repaired.")
        return 2 if args.strict else 0

    try:
        device_count = torch.cuda.device_count()
        print(f"[cuda] torch.cuda.device_count()={device_count}")
        if device_count:
            print(f"[cuda] torch.cuda.get_device_name(0)={torch.cuda.get_device_name(0)}")
            print(f"[cuda] torch.cuda.get_device_capability(0)={torch.cuda.get_device_capability(0)}")
    except Exception as exc:
        print(f"[cuda] torch CUDA enumeration failed: {exc.__class__.__name__}: {exc}")
        return 1

    try:
        import ctranslate2
        print(f"[cuda] ctranslate2={ctranslate2.__version__}")
        get_count = getattr(ctranslate2, "get_cuda_device_count", None)
        if get_count is not None:
            print(f"[cuda] ctranslate2.get_cuda_device_count()={get_count()}")
    except Exception as exc:
        print(f"[cuda] ctranslate2 import/probe failed: {exc.__class__.__name__}: {exc}")
        return 1

    cudnn_available = cudnn.is_available()
    print(f"[cuda] cudnn.is_available()={cudnn_available}")
    if not cudnn_available:
        print("[cuda] CUDA is visible, but cuDNN is unavailable.")
        return 1

    try:
        acceptable = cudnn.is_acceptable(torch.tensor(1.0, device="cuda"))
    except Exception as exc:
        print(f"[cuda] cudnn.is_acceptable() failed: {exc.__class__.__name__}: {exc}")
        return 1
    print(f"[cuda] cudnn.is_acceptable(tensor_on_cuda)={acceptable}")

    if not acceptable:
        print("[cuda] CUDA is visible, but cuDNN is not acceptable for inference.")
        return 1

    try:
        torch.empty((1,), device="cuda")
        print("[cuda] tiny CUDA allocation=ok")
    except Exception as exc:
        print(f"[cuda] tiny CUDA allocation failed: {exc.__class__.__name__}: {exc}")
        return 1

    print("[cuda] CUDA and cuDNN are ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
