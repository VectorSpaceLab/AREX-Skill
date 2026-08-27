#!/usr/bin/env python3
"""Report Kornia runtime, backend, and optional dependency availability."""

from __future__ import annotations

import argparse
import importlib
import json
import platform
from importlib.metadata import PackageNotFoundError, version


def dist_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def module_available(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-optional", action="store_true", help="probe common optional dependency modules")
    args = parser.parse_args()

    import torch
    import kornia

    report: dict[str, object] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "kornia": getattr(kornia, "__version__", dist_version("kornia")),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "mps_available": bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()),
        "distributions": {
            "kornia": dist_version("kornia"),
            "kornia-rs": dist_version("kornia-rs"),
            "numpy": dist_version("numpy"),
            "torch": dist_version("torch"),
        },
    }
    if torch.cuda.is_available():
        report["cuda"] = {
            "torch_cuda": torch.version.cuda,
            "device": torch.cuda.get_device_name(0),
            "capability": torch.cuda.get_device_capability(0),
        }
    if args.check_optional:
        optional = ["onnx", "onnxruntime", "onnxscript", "PIL", "cv2", "ivy", "tensorflow", "jax", "transformers", "diffusers"]
        report["optional_modules"] = {name: module_available(name) for name in optional}

    print(json.dumps(report, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
