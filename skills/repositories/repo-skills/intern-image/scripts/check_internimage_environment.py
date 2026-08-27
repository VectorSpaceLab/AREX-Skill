#!/usr/bin/env python3
"""Safe InternImage environment/backend diagnostic.

This script imports lightweight modules by name, checks tool availability, and
prints guidance for the selected InternImage workflow profiles. It never trains,
evaluates, downloads, builds DCNv3, launches distributed jobs, or imports local
repo code by path.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class Requirement:
    module: str
    distribution: Optional[str]
    purpose: str
    profiles: tuple[str, ...]
    optional: bool = False


REQUIREMENTS = [
    Requirement("torch", "torch", "PyTorch model execution and CUDA probe", ("classification", "detection", "segmentation", "autonomous", "deployment")),
    Requirement("torchvision", "torchvision", "image transforms and model stack compatibility", ("classification", "detection", "segmentation")),
    Requirement("timm", "timm", "InternImage model layers", ("classification", "detection", "segmentation", "autonomous")),
    Requirement("yacs", "yacs", "classification YACS config parser", ("classification",)),
    Requirement("yaml", "PyYAML", "YAML config loading", ("classification",)),
    Requirement("PIL", "Pillow", "classification feature extraction and Hugging Face image loading", ("classification",), optional=True),
    Requirement("transformers", "transformers", "Hugging Face InternImage usage", ("classification",), optional=True),
    Requirement("mmcv", "mmcv-full", "OpenMMLab 1.x/2.x-era runtime", ("detection", "segmentation", "autonomous", "deployment")),
    Requirement("mmdet", "mmdet", "MMDetection detection stack", ("detection", "autonomous", "deployment")),
    Requirement("mmseg", "mmsegmentation", "MMSegmentation segmentation stack", ("segmentation", "autonomous", "deployment")),
    Requirement("mmdet3d", "mmdet3d", "autonomous-driving mmdet3d baselines", ("autonomous",), optional=True),
    Requirement("deepspeed", "deepspeed", "classification large-model DeepSpeed path", ("classification",), optional=True),
    Requirement("accelerate", "accelerate", "classification Accelerate/DeepSpeed launch path", ("classification",), optional=True),
    Requirement("segment_anything", "segment-anything", "SAM-prompted instance segmentation", ("detection",), optional=True),
    Requirement("mmdeploy", "mmdeploy", "ONNX/TensorRT export", ("deployment",), optional=True),
    Requirement("tensorrt", "tensorrt", "TensorRT Python bindings", ("deployment",), optional=True),
    Requirement("openlanev2", "openlanev2", "OpenLane-V2 devkit", ("autonomous",), optional=True),
    Requirement("iso3166", "iso3166", "OpenLane-V2 country-code validation", ("autonomous",), optional=True),
]

PROFILES = ["classification", "detection", "segmentation", "autonomous", "deployment"]


def run_command(argv: List[str], timeout: float = 5.0) -> Dict[str, object]:
    try:
        proc = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return {"available": proc.returncode == 0, "returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    except FileNotFoundError:
        return {"available": False, "returncode": None, "stdout": "", "stderr": "not found"}
    except subprocess.TimeoutExpired:
        return {"available": False, "returncode": None, "stdout": "", "stderr": "timeout"}


def module_status(req: Requirement) -> Dict[str, object]:
    result: Dict[str, object] = {"module": req.module, "distribution": req.distribution, "purpose": req.purpose, "optional": req.optional}
    try:
        mod = importlib.import_module(req.module)
        result["import"] = "ok"
        result["module_file"] = getattr(mod, "__file__", None)
    except Exception as exc:
        result["import"] = "failed"
        result["error"] = f"{type(exc).__name__}: {exc}"
    if req.distribution:
        try:
            result["version"] = metadata.version(req.distribution)
        except Exception as exc:
            result["version_error"] = f"{type(exc).__name__}: {exc}"
    return result


def torch_backend_status() -> Dict[str, object]:
    try:
        import torch  # type: ignore
    except Exception as exc:
        return {"import": "failed", "error": f"{type(exc).__name__}: {exc}"}
    info: Dict[str, object] = {
        "import": "ok",
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda_version": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0,
    }
    if info["cuda_available"]:
        try:
            info["cuda_device_0"] = torch.cuda.get_device_name(0)
            info["cuda_capability_0"] = torch.cuda.get_device_capability(0)
            # Tiny allocation: safe but enough to prove the selected torch backend can touch CUDA.
            torch.empty((1,), device="cuda")
            info["cuda_tiny_allocation"] = "ok"
        except Exception as exc:
            info["cuda_tiny_allocation"] = f"failed: {type(exc).__name__}: {exc}"
    return info


def collect(args: argparse.Namespace) -> Dict[str, object]:
    selected = set(args.profile or PROFILES)
    reqs = [req for req in REQUIREMENTS if selected.intersection(req.profiles)]
    seen = set()
    filtered: List[Requirement] = []
    for req in reqs:
        key = (req.module, req.distribution)
        if key not in seen:
            seen.add(key)
            filtered.append(req)

    tools = {name: shutil.which(name) for name in ["python", "pip", "conda", "mim", "nvidia-smi", "nvcc", "cmake", "make", "gcc", "g++"]}
    result: Dict[str, object] = {
        "profiles": sorted(selected),
        "python": {"executable": sys.executable, "version": sys.version, "platform": platform.platform(), "machine": platform.machine()},
        "tools": tools,
        "modules": [module_status(req) for req in filtered],
        "torch_backend": torch_backend_status() if any(req.module == "torch" for req in filtered) else None,
        "nvidia_smi": run_command(["nvidia-smi", "--query-gpu=name,memory.total,driver_version,compute_cap", "--format=csv,noheader,nounits"]) if tools.get("nvidia-smi") else {"available": False, "stderr": "not found"},
        "environment_variables": {name: os.environ.get(name) for name in ["CUDA_HOME", "CUDA_PATH", "TENSORRT_DIR", "CUDNN_DIR", "MMDEPLOY_DIR"] if os.environ.get(name)},
    }
    return result


def print_text(report: Dict[str, object]) -> None:
    print("InternImage environment diagnostic")
    print("Profiles:", ", ".join(report["profiles"]))
    py = report["python"]
    print(f"Python: {py['executable']} | {py['version'].splitlines()[0]} | {py['machine']}")
    print("\nTools:")
    for name, path in report["tools"].items():
        print(f"  {name}: {path or 'missing'}")
    print("\nModules:")
    for item in report["modules"]:
        status = item.get("import")
        opt = " optional" if item.get("optional") else ""
        version = item.get("version") or item.get("version_error", "")
        print(f"  {item['module']}{opt}: {status} {version}")
        if status != "ok":
            print(f"    {item.get('error')}")
    if report.get("torch_backend"):
        print("\nTorch/CUDA:")
        for key, value in report["torch_backend"].items():
            print(f"  {key}: {value}")
    print("\nNVIDIA probe:")
    nvidia = report["nvidia_smi"]
    if nvidia.get("available"):
        print(nvidia.get("stdout", ""))
    else:
        print(f"  unavailable: {nvidia.get('stderr')}")
    if report.get("environment_variables"):
        print("\nDeployment environment variables:")
        for name in sorted(report["environment_variables"]):
            print(f"  {name}: set")

    print("\nInterpretation:")
    print("- Missing optional modules block only the workflows that need them.")
    print("- CUDA model execution requires torch CUDA availability and usually DCNv3; DCNv3 source builds also require nvcc/CUDA_HOME.")
    print("- TensorRT export requires mmdeploy, TensorRT/CUDNN variables or install paths, and the DCNv3 TensorRT custom op.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check InternImage workflow dependencies and backend signals without executing repo workloads.")
    parser.add_argument("--profile", action="append", choices=PROFILES, help="Workflow profile to check. Repeatable. Defaults to all profiles.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = collect(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
