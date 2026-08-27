#!/usr/bin/env python3
"""Read-only Det3D backend and optional-dependency diagnostic."""
from __future__ import annotations
import importlib.util
import json
import platform
import shutil
import subprocess
import sys


def present(name):
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def main() -> int:
    report = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "nvcc": shutil.which("nvcc"),
        "modules": {n: present(n) for n in ["det3d", "torch", "spconv", "yaml", "easydict", "addict", "cv2", "nuscenes", "lyft_dataset_sdk", "vtk", "open3d"]},
    }
    if present("torch"):
        import torch
        report["torch"] = {"version": torch.__version__, "cuda_build": torch.version.cuda, "cuda_available": torch.cuda.is_available(), "device_count": torch.cuda.device_count()}
        if torch.cuda.is_available():
            try:
                report["torch"]["device_0"] = torch.cuda.get_device_name(0)
                report["torch"]["tensor_smoke"] = int(torch.arange(5, device="cuda").sum().item()) == 10
            except Exception as exc:
                report["torch"]["tensor_smoke_error"] = f"{type(exc).__name__}: {exc}"
    if report["nvcc"]:
        p = subprocess.run([report["nvcc"], "--version"], text=True, capture_output=True)
        report["nvcc_version"] = (p.stdout or p.stderr).strip().splitlines()[-1:]
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
