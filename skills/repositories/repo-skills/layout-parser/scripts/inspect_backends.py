#!/usr/bin/env python3
"""Inspect LayoutParser runtime backends and optional dependencies.

This is a read-only helper for quickly checking which LayoutParser backends
are importable in the active environment.
"""
from __future__ import annotations

import argparse
import json
import shutil
from importlib import metadata

from layoutparser.file_utils import (
    is_detectron2_available,
    is_effdet_available,
    is_gcv_available,
    is_paddle_available,
    is_pytesseract_available,
    is_torch_available,
    is_torch_cuda_available,
)


def _version(dist_name: str):
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def inspect_backends() -> dict:
    pkg_resources_path = None
    try:
        import pkg_resources  # type: ignore

        pkg_resources_path = pkg_resources.__file__
    except Exception as exc:  # pragma: no cover - defensive only
        pkg_resources_path = f"{type(exc).__name__}: {exc}"

    torch_info = {
        "installed": is_torch_available(),
        "cuda_available": is_torch_cuda_available(),
        "version": _version("torch"),
        "torchvision": _version("torchvision"),
    }

    if torch_info["installed"]:
        import torch

        torch_info["cuda_device_count"] = torch.cuda.device_count()
        if torch.cuda.is_available():
            torch_info["cuda_device_name_0"] = torch.cuda.get_device_name(0)
            torch_info["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))

    return {
        "layoutparser": _version("layoutparser"),
        "pkg_resources": pkg_resources_path,
        "torch": torch_info,
        "backends": {
            "detectron2": {
                "available": is_detectron2_available(),
                "version": _version("detectron2"),
            },
            "effdet": {
                "available": is_effdet_available(),
                "version": _version("effdet"),
            },
            "paddle": {
                "available": is_paddle_available(),
                "version": _version("paddlepaddle"),
            },
            "pytesseract": {
                "available": is_pytesseract_available(),
                "version": _version("pytesseract"),
            },
            "google-cloud-vision": {
                "available": is_gcv_available(),
                "version": _version("google-cloud-vision"),
            },
        },
        "system": {
            "tesseract_binary": shutil.which("tesseract"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    data = inspect_backends()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"layoutparser: {data['layoutparser']}")
        print(f"pkg_resources: {data['pkg_resources']}")
        print("torch:")
        for key, value in data["torch"].items():
            print(f"  {key}: {value}")
        print("backends:")
        for name, info in data["backends"].items():
            print(f"  {name}: available={info['available']}, version={info['version']}")
        print(f"tesseract_binary: {data['system']['tesseract_binary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
