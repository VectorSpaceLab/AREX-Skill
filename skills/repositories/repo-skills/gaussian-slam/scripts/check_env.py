#!/usr/bin/env python3
"""Read-only Gaussian-SLAM environment diagnostic.

This helper checks Python/Torch/CUDA, expected optional packages, and the two
compiled extensions. It never installs packages, downloads data, or launches a
SLAM/evaluation job.
"""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys


def check_module(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
        return {"module": name, "ok": True, "version": getattr(module, "__version__", None)}
    except Exception as exc:  # diagnostic output should remain actionable
        return {"module": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "nvcc": shutil.which("nvcc"),
        "modules": [],
        "cuda": {"available": False},
    }
    module_names = [
        "torch", "torchvision", "open3d", "faiss", "cv2", "wandb",
        "trimesh", "pytorch_msssim", "torchmetrics", "plyfile",
        "simple_knn._C", "gaussian_rasterizer._C",
    ]
    report["modules"] = [check_module(name) for name in module_names]

    try:
        import torch

        cuda = {
            "available": bool(torch.cuda.is_available()),
            "torch_version": torch.__version__,
            "runtime": torch.version.cuda,
            "device_count": torch.cuda.device_count(),
        }
        if cuda["available"]:
            cuda["device_name"] = torch.cuda.get_device_name(0)
            cuda["capability"] = ".".join(map(str, torch.cuda.get_device_capability(0)))
            torch.empty((1,), device="cuda")
            cuda["allocation_smoke"] = "passed"
        report["cuda"] = cuda
    except Exception as exc:
        report["cuda"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    required = ["torch", "simple_knn._C", "gaussian_rasterizer._C"]
    module_results = {item["module"]: item for item in report["modules"]}
    ok = bool(report["cuda"].get("available")) and all(
        bool(module_results[name]["ok"]) for name in required
    )
    report["ok"] = ok
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']} ({report['python_executable']})")
        print(f"nvcc: {report['nvcc'] or 'not found'}")
        print(f"CUDA: {report['cuda']}")
        for item in report["modules"]:
            print(f"{item['module']}: {'OK' if item['ok'] else 'FAIL'}")
            if not item["ok"]:
                print(f"  {item['error']}")
        print("Gaussian-SLAM runtime preflight:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
