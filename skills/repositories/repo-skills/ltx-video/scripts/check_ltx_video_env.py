#!/usr/bin/env python3
"""Safe, no-download LTX-Video environment preflight."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
from typing import Any


PACKAGE_DISTRIBUTION = "ltx-video"
BASE_MODULE = "ltx_video"
DEEP_MODULES = (
    "ltx_video.inference",
    "ltx_video.pipelines.pipeline_ltx_video",
    "ltx_video.schedulers.rf",
    "ltx_video.models.autoencoders.causal_video_autoencoder",
    "ltx_video.models.transformers.transformer3d",
)
OPTIONAL_MEDIA_MODULES = ("imageio", "av", "torchvision")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect Python, LTX-Video imports, optional inference modules, and "
            "the PyTorch backend without downloading models or running generation."
        )
    )
    parser.add_argument(
        "--deep-imports",
        action="store_true",
        help="also import representative inference, pipeline, scheduler, VAE, and transformer modules",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit one machine-readable JSON object"
    )
    parser.add_argument(
        "--require-package",
        action="store_true",
        help="exit nonzero if the ltx_video package or requested deep imports fail",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="exit nonzero unless PyTorch imports and reports at least one CUDA device",
    )
    return parser.parse_args()


def distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def module_probe(name: str, do_import: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "module": name,
        "available": importlib.util.find_spec(name) is not None,
        "imported": False,
        "error": None,
    }
    if do_import and result["available"]:
        try:
            importlib.import_module(name)
            result["imported"] = True
        except Exception as exc:  # environment diagnostics must retain the real failure
            result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def torch_probe() -> dict[str, Any]:
    result: dict[str, Any] = {
        "available": importlib.util.find_spec("torch") is not None,
        "version": distribution_version("torch"),
        "imported": False,
        "cuda_build": None,
        "cuda_available": False,
        "cuda_device_count": 0,
        "cuda_devices": [],
        "mps_available": False,
        "error": None,
    }
    if not result["available"]:
        return result

    try:
        torch = importlib.import_module("torch")
        result["imported"] = True
        result["version"] = getattr(torch, "__version__", result["version"])
        result["cuda_build"] = getattr(getattr(torch, "version", None), "cuda", None)
        result["cuda_available"] = bool(torch.cuda.is_available())
        if result["cuda_available"]:
            count = int(torch.cuda.device_count())
            result["cuda_device_count"] = count
            for index in range(count):
                device: dict[str, Any] = {
                    "index": index,
                    "name": torch.cuda.get_device_name(index),
                }
                try:
                    device["capability"] = list(torch.cuda.get_device_capability(index))
                except Exception as exc:
                    device["capability_error"] = f"{type(exc).__name__}: {exc}"
                result["cuda_devices"].append(device)
        mps = getattr(getattr(torch, "backends", None), "mps", None)
        result["mps_available"] = bool(mps and mps.is_available())
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def build_report(deep_imports: bool) -> dict[str, Any]:
    base = module_probe(BASE_MODULE, do_import=True)
    deep = [module_probe(name, do_import=True) for name in DEEP_MODULES] if deep_imports else []
    media = [module_probe(name, do_import=False) for name in OPTIONAL_MEDIA_MODULES]
    return {
        "checker": "check_ltx_video_env",
        "safe": True,
        "downloads_models": False,
        "runs_generation": False,
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
            "supported": sys.version_info >= (3, 10),
            "platform": platform.platform(),
        },
        "ltx_video": {
            "distribution": PACKAGE_DISTRIBUTION,
            "distribution_version": distribution_version(PACKAGE_DISTRIBUTION),
            "base_import": base,
            "deep_imports_requested": deep_imports,
            "deep_imports": deep,
        },
        "optional_inference_modules": media,
        "torch": torch_probe(),
    }


def failures(report: dict[str, Any], args: argparse.Namespace) -> list[str]:
    problems: list[str] = []
    if args.require_package:
        base = report["ltx_video"]["base_import"]
        if not base["available"] or not base["imported"] or base["error"]:
            problems.append("required ltx_video base import failed")
        for item in report["ltx_video"]["deep_imports"]:
            if not item["available"] or not item["imported"] or item["error"]:
                problems.append(f"required deep import failed: {item['module']}")
    if args.require_cuda:
        torch = report["torch"]
        if not torch["imported"]:
            problems.append("required PyTorch import failed")
        elif not torch["cuda_available"] or torch["cuda_device_count"] < 1:
            problems.append("required CUDA device is unavailable")
    return problems


def print_human(report: dict[str, Any], problems: list[str]) -> None:
    python = report["python"]
    package = report["ltx_video"]
    base = package["base_import"]
    torch = report["torch"]

    print("LTX-Video environment preflight (no downloads, no generation)")
    print(f"Python: {python['version']} ({python['executable']})")
    print(f"Python >= 3.10: {'yes' if python['supported'] else 'no'}")
    print(f"ltx-video distribution: {package['distribution_version'] or 'not installed'}")
    if base["error"]:
        print(f"ltx_video import: failed ({base['error']})")
    else:
        print(f"ltx_video import: {'ok' if base['imported'] else 'not available'}")

    for item in package["deep_imports"]:
        status = "ok" if item["imported"] and not item["error"] else "failed"
        detail = f" ({item['error']})" if item["error"] else ""
        print(f"deep import {item['module']}: {status}{detail}")

    media = ", ".join(
        f"{item['module']}={'yes' if item['available'] else 'no'}"
        for item in report["optional_inference_modules"]
    )
    print(f"Optional inference modules: {media}")
    if torch["error"]:
        print(f"PyTorch: import failed ({torch['error']})")
    elif not torch["imported"]:
        print("PyTorch: not installed")
    else:
        print(f"PyTorch: {torch['version']} (CUDA build: {torch['cuda_build'] or 'none'})")
        print(
            "CUDA: "
            f"{'available' if torch['cuda_available'] else 'unavailable'}; "
            f"devices={torch['cuda_device_count']}"
        )
        for device in torch["cuda_devices"]:
            capability = device.get("capability", "unknown")
            print(f"  [{device['index']}] {device['name']} capability={capability}")
        print(f"MPS: {'available' if torch['mps_available'] else 'unavailable'}")

    if problems:
        print("Required checks failed:")
        for problem in problems:
            print(f"- {problem}")
    else:
        print("Result: no requested hard requirement failed")


def main() -> int:
    args = parse_args()
    report = build_report(args.deep_imports)
    problems = failures(report, args)
    report["required_failures"] = problems
    report["ok"] = not problems
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report, problems)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
