#!/usr/bin/env python3
"""Report imgclsmob backend/provider availability without installation or downloads."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys


SURFACES = {
    "mxnet": {"distribution": "mxnet", "imports": ["mxnet"]},
    "gluoncv2": {"distribution": "gluoncv2", "imports": ["gluoncv2", "gluoncv2.model_provider"]},
    "torch": {"distribution": "torch", "imports": ["torch"]},
    "torchvision": {"distribution": "torchvision", "imports": ["torchvision"]},
    "pytorchcv": {"distribution": "pytorchcv", "imports": ["pytorchcv", "pytorchcv.model_provider"]},
    "tensorflow": {"distribution": "tensorflow", "imports": ["tensorflow"]},
    "tf2cv": {"distribution": "tf2cv", "imports": ["tf2cv", "tf2cv.model_provider"]},
    "tensorflowcv": {"distribution": "tensorflowcv", "imports": ["tensorflowcv", "tensorflowcv.model_provider"]},
    "kerascv": {"distribution": "kerascv", "imports": ["kerascv", "kerascv.model_provider"]},
    "chainercv2": {"distribution": "chainercv2", "imports": ["chainercv2", "chainercv2.model_provider"]},
}


def distribution_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "missing"


def probe_import(name: str) -> dict[str, str]:
    try:
        module = importlib.import_module(name)
        return {"status": "available", "module": getattr(module, "__name__", name)}
    except Exception as exc:  # noqa: BLE001 - report the actual import boundary
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


def inspect_environment() -> dict[str, object]:
    result: dict[str, object] = {"network": "not_used", "surfaces": {}}
    surfaces: dict[str, object] = result["surfaces"]  # type: ignore[assignment]
    for surface, spec in SURFACES.items():
        surfaces[surface] = {
            "distribution": spec["distribution"],
            "version": distribution_version(spec["distribution"]),
            "imports": {name: probe_import(name) for name in spec["imports"]},
        }
    try:
        import torch

        surfaces["torch_device"] = {
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()),
        }
    except Exception as exc:  # noqa: BLE001
        surfaces["torch_device"] = {"status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}
    try:
        import mxnet as mx

        surfaces["mxnet_device"] = {"num_gpus": int(mx.context.num_gpus()), "cpu": str(mx.cpu())}
    except Exception as exc:  # noqa: BLE001
        surfaces["mxnet_device"] = {"status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Probe imgclsmob package/provider availability without installation or network access.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="emit one JSON object")
    args = parser.parse_args(argv)
    result = inspect_environment()
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        for name, value in result["surfaces"].items():
            if isinstance(value, dict) and "version" in value:
                print(f"{name}: distribution={value['version']}")
                for module, probe in value["imports"].items():
                    print(f"  import {module}: {probe['status']}")
                    if "error" in probe:
                        print(f"    {probe['error']}")
            else:
                print(f"{name}: {value}")
        print("network: not_used")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
