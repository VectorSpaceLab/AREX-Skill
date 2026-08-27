#!/usr/bin/env python3
"""Print a JSON summary of fastMRI import and backend readiness."""

import importlib
import importlib.metadata as metadata
import json
import sys

PACKAGES = [
    ("fastmri", "fastmri"),
    ("torch", "torch"),
    ("torchvision", "torchvision"),
    ("h5py", "h5py"),
    ("numpy", "numpy"),
    ("scikit-image", "skimage"),
    ("runstats", "runstats"),
    ("pytorch-lightning", "pytorch_lightning"),
    ("torchmetrics", "torchmetrics"),
    ("pandas", "pandas"),
    ("PyYAML", "yaml"),
    ("requests", "requests"),
]

SUBMODULES = ["fastmri.data", "fastmri.models", "fastmri.pl_modules"]


def package_status(distribution_name, import_name):
    result = {"distribution": distribution_name, "import": import_name}
    try:
        result["version"] = metadata.version(distribution_name)
    except metadata.PackageNotFoundError:
        result["version"] = None
    try:
        module = importlib.import_module(import_name)
        result["import_ok"] = True
        result["module_version"] = getattr(module, "__version__", None)
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        result["import_ok"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main():
    packages = {dist: package_status(dist, mod) for dist, mod in PACKAGES}
    submodules = {}
    for name in SUBMODULES:
        try:
            importlib.import_module(name)
            submodules[name] = {"import_ok": True}
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            submodules[name] = {"import_ok": False, "error": f"{type(exc).__name__}: {exc}"}

    backend = {"cuda_available": None, "cuda_device_count": None}
    torch_status = packages.get("torch", {})
    if torch_status.get("import_ok"):
        import torch

        backend["cuda_available"] = bool(torch.cuda.is_available())
        backend["cuda_device_count"] = int(torch.cuda.device_count())

    summary = {
        "python": sys.version,
        "packages": packages,
        "submodules": submodules,
        "backend": backend,
        "notes": [
            "fastmri.data imports requests in this checkout; install requests if that submodule fails.",
            "GPU execution is optional for many smoke checks; long training and pretrained inference may need user-provided hardware/checkpoints.",
        ],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if packages["fastmri"].get("import_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
