#!/usr/bin/env python3
"""Check a GluonCV installation without downloading models or running training.

The script reports package/backend versions, GluonCV backend discovery, model
registry counts when importable, and known legacy compatibility warnings. It is
safe by default and performs no network access. Use --cuda-smoke only when a
CUDA-capable backend is expected and a tiny device allocation is acceptable.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any, Dict, Optional


def dist_version(name: str) -> Optional[str]:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def module_version(name: str) -> Optional[str]:
    try:
        mod = importlib.import_module(name)
    except Exception:
        return None
    return getattr(mod, "__version__", None)


def try_import(name: str) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(name)
        return {"ok": True, "version": getattr(mod, "__version__", None), "error": None}
    except Exception as exc:  # pragma: no cover - diagnostic output path
        return {"ok": False, "version": None, "error": f"{type(exc).__name__}: {exc}"}


def cuda_smoke() -> Dict[str, Any]:
    result: Dict[str, Any] = {"torch": None, "mxnet": None}
    try:
        import torch

        torch_result: Dict[str, Any] = {
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
            "cuda_version": torch.version.cuda,
        }
        if torch.cuda.is_available():
            torch.empty((1,), device="cuda")
            torch_result["device_name"] = torch.cuda.get_device_name(0)
            torch_result["allocation"] = "passed"
        result["torch"] = torch_result
    except Exception as exc:  # pragma: no cover
        result["torch"] = {"error": f"{type(exc).__name__}: {exc}"}

    try:
        import mxnet as mx

        mx_result: Dict[str, Any] = {"gpu0_available": False}
        try:
            x = mx.nd.zeros((1,), ctx=mx.gpu(0))
            x.wait_to_read()
            mx_result["gpu0_available"] = True
            mx_result["allocation"] = "passed"
        except Exception as exc:  # pragma: no cover
            mx_result["error"] = f"{type(exc).__name__}: {exc}"
        result["mxnet"] = mx_result
    except Exception as exc:  # pragma: no cover
        result["mxnet"] = {"error": f"{type(exc).__name__}: {exc}"}
    return result


def collect(cuda: bool = False) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {
            "gluoncv": dist_version("gluoncv"),
            "mxnet": dist_version("mxnet"),
            "torch": dist_version("torch"),
            "torchvision": dist_version("torchvision"),
            "numpy": dist_version("numpy"),
            "Pillow": dist_version("Pillow"),
        },
        "imports": {},
        "gluoncv": {},
        "registries": {},
        "warnings": [],
    }

    for name in ["mxnet", "torch", "torchvision", "PIL", "gluoncv"]:
        report["imports"][name] = try_import(name)

    gcv_info = report["imports"].get("gluoncv", {})
    if gcv_info.get("ok"):
        import gluoncv

        report["gluoncv"] = {
            "version": getattr(gluoncv, "__version__", None),
            "found_mxnet": bool(getattr(gluoncv, "_found_mxnet", False)),
            "found_pytorch": bool(getattr(gluoncv, "_found_pytorch", False)),
        }
        if report["gluoncv"]["found_mxnet"] and report["gluoncv"]["found_pytorch"]:
            report["warnings"].append("Both MXNet and PyTorch are installed; GluonCV warns about increased GPU memory footprint in mixed-backend environments.")
        try:
            from gluoncv import model_zoo

            report["registries"]["mxnet_model_zoo_count"] = len(list(model_zoo.get_model_list()))
        except Exception as exc:  # pragma: no cover
            report["registries"]["mxnet_model_zoo_error"] = f"{type(exc).__name__}: {exc}"
        try:
            from gluoncv.torch.model_zoo import get_model_list

            report["registries"]["torch_model_zoo_count"] = len(list(get_model_list()))
        except Exception as exc:  # pragma: no cover
            report["registries"]["torch_model_zoo_error"] = f"{type(exc).__name__}: {exc}"

    numpy_v = report["distributions"].get("numpy")
    mxnet_v = report["distributions"].get("mxnet")
    if mxnet_v and numpy_v:
        try:
            major_minor = tuple(int(p) for p in numpy_v.split(".")[:2])
            if major_minor >= (1, 24):
                report["warnings"].append("MXNet 1.x often fails with NumPy >=1.24; prefer numpy<1.24 for GluonCV MXNet workflows.")
        except Exception:
            pass
    pillow_v = report["distributions"].get("Pillow")
    if pillow_v:
        try:
            major = int(pillow_v.split(".")[0])
            if major >= 10:
                report["warnings"].append("GluonCV Torch transforms may fail with Pillow>=10 because legacy code references PIL.Image.LINEAR; prefer Pillow<10.")
        except Exception:
            pass

    if cuda:
        report["cuda_smoke"] = cuda_smoke()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check GluonCV import/backend readiness without downloads or training.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    parser.add_argument("--cuda-smoke", action="store_true", help="Attempt tiny CUDA allocations for installed backends.")
    args = parser.parse_args()

    report = collect(cuda=args.cuda_smoke)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print("Distributions:")
        for key, value in report["distributions"].items():
            print(f"  {key}: {value or 'not installed'}")
        print("Imports:")
        for key, value in report["imports"].items():
            status = "ok" if value.get("ok") else "failed"
            suffix = f" ({value.get('error')})" if value.get("error") else ""
            print(f"  {key}: {status}{suffix}")
        if report.get("gluoncv"):
            print("GluonCV backend discovery:")
            print(f"  version: {report['gluoncv'].get('version')}")
            print(f"  found_mxnet: {report['gluoncv'].get('found_mxnet')}")
            print(f"  found_pytorch: {report['gluoncv'].get('found_pytorch')}")
        if report.get("registries"):
            print("Registries:")
            for key, value in report["registries"].items():
                print(f"  {key}: {value}")
        if report.get("cuda_smoke"):
            print("CUDA smoke:")
            print(json.dumps(report["cuda_smoke"], indent=2, sort_keys=True))
        if report["warnings"]:
            print("Warnings:")
            for warning in report["warnings"]:
                print(f"  - {warning}")
    return 0 if report["imports"].get("gluoncv", {}).get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
