#!/usr/bin/env python3
"""Safe environment checker for HunyuanImage-3.0.

The checker imports packages and optionally verifies CUDA. It never loads model
weights, starts services, calls Tencent Cloud, or generates images.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

DISTRIBUTIONS = [
    "hunyuan-image-3",
    "torch",
    "torchvision",
    "transformers",
    "diffusers",
    "gradio",
]

IMPORTS = [
    "hunyuan_image_3",
    "hunyuan_image_3.system_prompt",
    "torch",
    "torchvision",
    "transformers",
    "diffusers",
]

OPTIONAL_IMPORTS = [
    "PE.deepseek",
    "vllm_infer.openai_client",
    "flashinfer",
    "flash_attn",
]


def distribution_versions() -> dict[str, str]:
    out: dict[str, str] = {}
    for dist in DISTRIBUTIONS:
        try:
            out[dist] = version(dist)
        except PackageNotFoundError:
            out[dist] = "missing"
    return out


def import_status(modules: list[str]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for module in modules:
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 - diagnostic should capture exact failures
            out[module] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
        else:
            out[module] = {"status": "ok"}
    return out


def cuda_status() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"torch import failed: {type(exc).__name__}: {exc}"}

    info: dict[str, Any] = {
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda_runtime": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if torch.cuda.is_available():
        try:
            tensor = torch.empty((1,), device="cuda")
            info.update(
                {
                    "status": "ok",
                    "device_name_0": torch.cuda.get_device_name(0),
                    "device_capability_0": list(torch.cuda.get_device_capability(0)),
                    "allocation_device": str(tensor.device),
                }
            )
        except Exception as exc:  # noqa: BLE001
            info.update({"status": "error", "error": f"cuda allocation failed: {type(exc).__name__}: {exc}"})
    else:
        info["status"] = "unavailable"
    return info


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe HunyuanImage-3.0 import and CUDA checker")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA is unavailable or allocation fails")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)

    report = {
        "distributions": distribution_versions(),
        "imports": import_status(IMPORTS),
        "optional_imports": import_status(OPTIONAL_IMPORTS),
        "cuda": cuda_status(),
    }

    hard_errors = [
        f"import {name}: {item['error']}"
        for name, item in report["imports"].items()
        if item["status"] != "ok"
    ]
    if args.require_cuda and report["cuda"].get("status") != "ok":
        hard_errors.append("CUDA required but not available: " + json.dumps(report["cuda"], sort_keys=True))

    report["status"] = "ok" if not hard_errors else "error"
    report["errors"] = hard_errors

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("# Distributions")
        for name, val in report["distributions"].items():
            print(f"{name}: {val}")
        print("\n# Required imports")
        for name, item in report["imports"].items():
            print(f"{name}: {item['status']}" + (f" ({item['error']})" if item['status'] != "ok" else ""))
        print("\n# Optional imports")
        for name, item in report["optional_imports"].items():
            print(f"{name}: {item['status']}" + (f" ({item['error']})" if item['status'] != "ok" else ""))
        print("\n# CUDA")
        for key, value in report["cuda"].items():
            print(f"{key}: {value}")
        print("\nSTATUS:", report["status"])
        for err in hard_errors:
            print("ERROR:", err)

    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
