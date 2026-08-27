#!/usr/bin/env python3
"""Check whether the current Python runtime is ready for Zero123Plus.

This checker does not load models and never downloads weights. It only verifies
imports, optional module groups, and CUDA availability.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import json
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ModuleSpec:
    module: str
    dist: str
    group: str
    required_core: bool
    install_hint: str


MODULES = [
    ModuleSpec("torch", "torch", "core", True, "Install a CUDA-capable torch wheel."),
    ModuleSpec("torchvision", "torchvision", "core", True, "Install torchvision matching torch."),
    ModuleSpec("diffusers", "diffusers", "core", True, "Install diffusers==0.20.2."),
    ModuleSpec("transformers", "transformers", "core", True, "Install transformers==4.29.2."),
    ModuleSpec("huggingface_hub", "huggingface-hub", "core", True, "Install huggingface-hub==0.18.0."),
    ModuleSpec("PIL", "Pillow", "core", True, "Install pillow."),
    ModuleSpec("numpy", "numpy", "core", True, "Install numpy==1.24.4 for the verified stack."),
    ModuleSpec("pymatting", "pymatting", "normal", False, "Install pymatting for normal postprocess."),
    ModuleSpec("scipy", "scipy", "normal", False, "Install scipy for normal postprocess."),
    ModuleSpec("rembg", "rembg", "background", False, "Install rembg==2.0.51 for background removal."),
    ModuleSpec("cv2", "opencv-contrib-python", "background", False, "Install opencv-contrib-python."),
    ModuleSpec("segment_anything", "segment-anything", "background", False, "Install segment-anything from its Git repository."),
    ModuleSpec("gradio", "gradio", "deployment", False, "Install gradio==3.50.2 for the demo launcher."),
    ModuleSpec("streamlit", "streamlit", "deployment", False, "Install streamlit==1.22.0 for the source-style demo."),
    ModuleSpec("cog", "cog", "deployment", False, "Install cog for Cog predictor templates."),
    ModuleSpec("accelerate", "accelerate", "optional", False, "Install accelerate==0.24.1 for SDXL helper/Cog parity."),
    ModuleSpec("requests", "requests", "optional", False, "Install requests for URL-backed example inputs."),
    ModuleSpec("fire", "fire", "optional", False, "Install fire for source-style CLI parity."),
]


GROUP_FLAGS = {
    "normal": "require_normal",
    "background": "require_background",
    "deployment": "require_deployment",
}


def _version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def _module_status(spec: ModuleSpec) -> dict:
    found = importlib.util.find_spec(spec.module) is not None
    return {
        "module": spec.module,
        "distribution": spec.dist,
        "group": spec.group,
        "found": found,
        "version": _version(spec.dist) if found else None,
        "install_hint": None if found else spec.install_hint,
    }


def _cuda_status() -> dict:
    if importlib.util.find_spec("torch") is None:
        return {"checked": False, "available": False, "reason": "torch missing"}
    import torch

    result = {
        "checked": True,
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda_runtime": getattr(torch.version, "cuda", None),
        "available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        "device0_name": None,
        "device0_capability": None,
        "tensor_allocation": False,
    }
    if torch.cuda.is_available():
        result["device0_name"] = torch.cuda.get_device_name(0)
        result["device0_capability"] = torch.cuda.get_device_capability(0)
        torch.empty((1,), device="cuda")
        result["tensor_allocation"] = True
    return result


def _is_required(spec: ModuleSpec, args) -> bool:
    if spec.required_core:
        return True
    flag = GROUP_FLAGS.get(spec.group)
    return bool(getattr(args, flag, False)) if flag else False


def build_report(args) -> dict:
    modules = [_module_status(spec) for spec in MODULES]
    cuda = _cuda_status()
    missing_required = []
    for spec, status in zip(MODULES, modules):
        if _is_required(spec, args) and not status["found"]:
            missing_required.append(spec.module)
    if args.require_cuda and not cuda.get("available"):
        missing_required.append("cuda")
    return {
        "status": "ok" if not missing_required else "failed",
        "missing_required": missing_required,
        "modules": modules,
        "cuda": cuda,
    }


def print_text(report: dict, args) -> None:
    print("Zero123Plus environment check")
    for item in report["modules"]:
        status = "ok" if item["found"] else "missing"
        suffix = f" ({item['version']})" if item["version"] else ""
        print(f"- {item['module']:<18} {status}{suffix} [{item['group']}]")
        if item["install_hint"]:
            print(f"  hint: {item['install_hint']}")

    cuda = report["cuda"]
    if cuda.get("available"):
        print(
            "- CUDA               ok "
            f"({cuda.get('device_count')} device(s), {cuda.get('device0_name')}, runtime {cuda.get('torch_cuda_runtime')})"
        )
    else:
        print("- CUDA               missing")
        if args.require_cuda:
            print("  hint: real Zero123Plus generation requires a CUDA-enabled torch runtime")

    if report["missing_required"]:
        print("Missing required checks: " + ", ".join(report["missing_required"]))
    else:
        print("All required checks passed.")


def parse_args(argv: Iterable[str] | None = None):
    parser = argparse.ArgumentParser(
        description="Check Zero123Plus runtime dependencies without loading models.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--check-only", action="store_true", help="Accepted for readability; the script is always check-only.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA is unavailable.")
    parser.add_argument("--require-normal", action="store_true", help="Require pymatting and scipy for normal postprocess.")
    parser.add_argument("--require-background", action="store_true", help="Require rembg, opencv, and segment-anything background-removal modules.")
    parser.add_argument("--require-deployment", action="store_true", help="Require Gradio, Streamlit, and Cog deployment modules.")
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of text.")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report, args)
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
