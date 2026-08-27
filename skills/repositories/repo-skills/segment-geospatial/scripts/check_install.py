#!/usr/bin/env python3
"""Safe install/backend diagnostic for segment-geospatial.

This helper imports package modules, prints model registry facts, optionally
checks optional model wrappers, and can require a CUDA torch allocation. It does
not download model weights, fetch map tiles, start a service, or require the
original repository checkout.

Examples:
    python scripts/check_install.py
    python scripts/check_install.py --check-optional --json
    python scripts/check_install.py --require-cuda
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def try_import(name: str) -> dict:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic should report import cause
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"name": name, "ok": True, "module": getattr(module, "__name__", name)}


def cuda_check(require: bool) -> tuple[dict, bool]:
    result: dict = {"requested": require, "torch_imported": False}
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result, not require

    result.update(
        {
            "torch_imported": True,
            "torch_version": getattr(torch, "__version__", None),
            "torch_cuda": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    )
    if torch.cuda.is_available():
        try:
            result["device_name_0"] = torch.cuda.get_device_name(0)
            tensor = torch.empty((1,), device="cuda")
            result["allocation"] = str(tensor.device)
        except Exception as exc:  # noqa: BLE001
            result["allocation_error"] = f"{type(exc).__name__}: {exc}"
            return result, not require
    return result, (not require) or bool(result.get("cuda_available"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-optional", action="store_true", help="Import optional wrappers that should not download weights.")
    parser.add_argument("--include-caption-network", action="store_true", help="Also import samgeo.caption, which fetches a remote aerial feature vocabulary at import time.")
    parser.add_argument("--require-cuda", action="store_true", help="Return non-zero unless CUDA is visible and a tiny torch allocation succeeds.")
    parser.add_argument("--strict-optional", action="store_true", help="Return non-zero if an optional import checked by this script fails.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable report.")
    args = parser.parse_args(argv)

    report: dict = {
        "distribution": {"segment-geospatial": package_version("segment-geospatial")},
        "required_imports": [],
        "optional_imports": [],
        "model_registry": None,
        "cuda": None,
        "notes": [],
    }

    required = [
        "samgeo",
        "samgeo.common",
        "samgeo.api",
        "samgeo.samgeo",
        "samgeo.samgeo2",
        "samgeo.samgeo3",
        "samgeo.model_registry",
        "samgeo.utmconv",
    ]
    for name in required:
        report["required_imports"].append(try_import(name))

    try:
        from samgeo.model_registry import AVAILABLE_MODELS, DEFAULT_MODEL_IDS, EXTRAS_MAP

        report["model_registry"] = {
            "default_model_ids": DEFAULT_MODEL_IDS,
            "available_models": AVAILABLE_MODELS,
            "extras_map": EXTRAS_MAP,
        }
    except Exception as exc:  # noqa: BLE001
        report["model_registry"] = {"error": f"{type(exc).__name__}: {exc}"}

    if args.check_optional:
        optional = ["samgeo.fast_sam", "samgeo.hq_sam", "samgeo.text_sam"]
        for name in optional:
            report["optional_imports"].append(try_import(name))
        if args.include_caption_network:
            report["optional_imports"].append(try_import("samgeo.caption"))
        else:
            report["notes"].append("Skipped samgeo.caption unless --include-caption-network is set; importing it fetches a remote aerial feature vocabulary.")
        report["notes"].append("detectree2 and FER/GDAL runtime paths are intentionally not instantiated by this safe check.")

    report["cuda"], cuda_ok = cuda_check(args.require_cuda)

    required_ok = all(item["ok"] for item in report["required_imports"])
    optional_ok = all(item["ok"] for item in report["optional_imports"]) if args.strict_optional else True
    exit_ok = required_ok and optional_ok and cuda_ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"segment-geospatial: {report['distribution']['segment-geospatial']}")
        print("Required imports:")
        for item in report["required_imports"]:
            status = "OK" if item["ok"] else f"FAIL ({item['error']})"
            print(f"  {item['name']}: {status}")
        if report["model_registry"]:
            print(f"Model registry: {report['model_registry']}")
        if args.check_optional:
            print("Optional imports:")
            for item in report["optional_imports"]:
                status = "OK" if item["ok"] else f"FAIL ({item['error']})"
                print(f"  {item['name']}: {status}")
        print(f"CUDA: {report['cuda']}")
        for note in report["notes"]:
            print(f"Note: {note}")

    return 0 if exit_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
