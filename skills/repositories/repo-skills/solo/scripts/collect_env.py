#!/usr/bin/env python3
"""Print safe SOLO/MMDetection environment diagnostics.

This helper intentionally performs imports and version/device probes only. It
never downloads weights/data, builds extensions, or changes files.
"""
from __future__ import annotations

import importlib
import platform
import sys


def probe(name: str) -> None:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", "unknown")
        location = getattr(module, "__file__", "unknown")
        print(f"{name}: import=ok version={version} location={location}")
    except Exception as exc:  # diagnostic output must continue
        print(f"{name}: import=error {type(exc).__name__}: {exc}")


def main() -> int:
    print(f"python: {sys.version.split()[0]} ({sys.executable})")
    print(f"platform: {platform.platform()}")
    probe("numpy")
    probe("torch")
    try:
        import torch

        print(f"torch.cuda.available: {torch.cuda.is_available()}")
        print(f"torch.version.cuda: {torch.version.cuda}")
        if torch.cuda.is_available():
            print(f"torch.cuda.devices: {torch.cuda.device_count()}")
            print(f"torch.cuda.device0: {torch.cuda.get_device_name(0)}")
    except Exception as exc:
        print(f"torch.cuda.probe: error {type(exc).__name__}: {exc}")
    probe("torchvision")
    probe("mmcv")
    probe("mmdet")
    for module in (
        "mmdet.models",
        "mmdet.datasets",
        "mmdet.apis",
        "mmdet.ops.nms",
        "mmdet.ops.roi_align",
        "mmdet.ops.dcn",
    ):
        probe(module)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
