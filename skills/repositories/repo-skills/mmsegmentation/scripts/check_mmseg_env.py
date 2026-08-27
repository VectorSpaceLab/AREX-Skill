#!/usr/bin/env python3
"""Check MMSegmentation import, version, and backend compatibility.

This script is read-only. It does not download checkpoints, run training, or
write outputs beyond stdout/stderr.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from packaging.version import Version, InvalidVersion


def _version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _import(name: str):
    try:
        module = importlib.import_module(name)
        return True, module, None
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, None, f"{type(exc).__name__}: {exc}"


def _parse_version(value: str | None) -> Version | None:
    if not value:
        return None
    try:
        return Version(value.split('+')[0])
    except InvalidVersion:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MMSegmentation runtime compatibility.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if torch CUDA is unavailable.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    checks: dict[str, object] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "imports": {},
        "distributions": {},
        "warnings": [],
        "errors": [],
    }

    for dist in ["mmsegmentation", "mmcv", "mmcv-lite", "mmengine", "torch", "numpy", "opencv-python"]:
        checks["distributions"][dist] = _version(dist)

    for module_name in ["mmseg", "mmcv", "mmengine", "torch", "numpy", "cv2"]:
        ok, module, error = _import(module_name)
        checks["imports"][module_name] = {
            "ok": ok,
            "version": getattr(module, "__version__", None) if module else None,
            "error": error,
        }
        if not ok and module_name in {"mmseg", "mmcv", "mmengine", "torch"}:
            checks["errors"].append(f"Required import failed: {module_name}: {error}")

    mmcv_version = checks["imports"].get("mmcv", {}).get("version")
    mmengine_version = checks["imports"].get("mmengine", {}).get("version")
    numpy_version = checks["imports"].get("numpy", {}).get("version")
    opencv_version = checks["imports"].get("cv2", {}).get("version")

    mmcv_v = _parse_version(mmcv_version)
    mmengine_v = _parse_version(mmengine_version)
    numpy_v = _parse_version(numpy_version)
    opencv_v = _parse_version(opencv_version)

    if mmcv_v and not (Version("2.0.0rc4") <= mmcv_v < Version("2.2.0")):
        checks["errors"].append(f"mmcv {mmcv_version} is outside MMSegmentation 1.2.x compatibility range >=2.0.0rc4,<2.2.0")
    if mmengine_v and not (Version("0.5.0") <= mmengine_v < Version("1.0.0")):
        checks["errors"].append(f"mmengine {mmengine_version} is outside MMSegmentation 1.2.x compatibility range >=0.5.0,<1.0.0")
    if checks["distributions"].get("mmcv-lite") and not checks["distributions"].get("mmcv"):
        checks["warnings"].append("mmcv-lite is installed without full mmcv; APIs needing mmcv._ext/mmcv.ops may fail.")
    if numpy_v and numpy_v >= Version("2"):
        checks["warnings"].append("numpy>=2 can be incompatible with older torch/mmcv wheels compiled against NumPy 1.x.")
    if numpy_v and numpy_v < Version("2") and opencv_v and opencv_v >= Version("4.12"):
        checks["warnings"].append("opencv-python>=4.12 may require numpy>=2; pin opencv-python<4.12 when using numpy<2.")

    torch_ok, torch_module, _ = _import("torch")
    cuda_info = {"available": False, "device_count": 0, "version_cuda": None}
    if torch_ok and torch_module is not None:
        cuda_info = {
            "available": bool(torch_module.cuda.is_available()),
            "device_count": int(torch_module.cuda.device_count()),
            "version_cuda": torch_module.version.cuda,
        }
        if cuda_info["available"] and cuda_info["device_count"]:
            try:
                cuda_info["device_name_0"] = torch_module.cuda.get_device_name(0)
            except Exception as exc:  # pragma: no cover
                cuda_info["device_name_error"] = f"{type(exc).__name__}: {exc}"
    checks["cuda"] = cuda_info
    if args.require_cuda and not cuda_info["available"]:
        checks["errors"].append("--require-cuda was set but torch.cuda.is_available() is False.")

    ok = not checks["errors"]
    checks["ok"] = ok

    if args.json:
        print(json.dumps(checks, indent=2, sort_keys=True))
    else:
        print(f"Python: {checks['python']} ({checks['executable']})")
        for module_name, item in checks["imports"].items():
            status = "OK" if item["ok"] else "FAIL"
            version = f" {item['version']}" if item.get("version") else ""
            error = f" - {item['error']}" if item.get("error") else ""
            print(f"{status} import {module_name}{version}{error}")
        print(f"CUDA: available={cuda_info['available']} devices={cuda_info['device_count']} torch_cuda={cuda_info['version_cuda']}")
        for warning in checks["warnings"]:
            print(f"WARNING: {warning}")
        for error in checks["errors"]:
            print(f"ERROR: {error}")
        print("Status:", "ok" if ok else "failed")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
