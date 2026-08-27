#!/usr/bin/env python3
"""Diagnostic checks for a Make-It-3D runtime environment.

This helper is intentionally read-only. It does not download model weights,
compile CUDA extensions, or import the repo's main.py. It checks common modules,
CUDA visibility, repo-file layout, and optional asset paths so an agent can
produce targeted setup advice before a long Make-It-3D run.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

MODULES = [
    ("torch", "core", True),
    ("torchvision", "core", True),
    ("cv2", "core", True),
    ("numpy", "core", True),
    ("scipy", "core", True),
    ("imageio", "core", True),
    ("timm", "dpt", True),
    ("diffusers", "stable-diffusion", True),
    ("transformers", "stable-diffusion/blip2", True),
    ("clip", "clip-guidance", True),
    ("tinycudann", "default-tcnn-backbone", False),
    ("pytorch3d", "refinement", False),
    ("contextual_loss", "refinement", False),
    ("open3d", "point-cloud-output", False),
    ("mcubes", "mesh-export", False),
    ("xatlas", "mesh-export", False),
    ("nvdiffrast", "mesh-export", False),
    ("tensorboardX", "logging", False),
    ("torch_ema", "training", False),
    ("trimesh", "visualization/export", False),
]

REPO_FILES = [
    "main.py",
    "requirements.txt",
    "nerf/provider.py",
    "nerf/utils.py",
    "nerf/network.py",
    "nerf/network_tcnn.py",
    "nerf/sd.py",
    "nerf/clip.py",
    "nerf/refine_utils.py",
    "nerf/renderer.py",
    "raymarching/setup.py",
    "raymarching/src/raymarching.cu",
    "DPT/run_monodepth.py",
    "DPT/dpt/models.py",
]


def import_status(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", None)
        return {"module": name, "ok": True, "version": version}
    except Exception as exc:  # noqa: BLE001 - diagnostic tool
        return {"module": name, "ok": False, "error_type": type(exc).__name__, "error": str(exc)[:300]}


def torch_status() -> Dict[str, Any]:
    try:
        import torch

        info: Dict[str, Any] = {
            "import_ok": True,
            "version": getattr(torch, "__version__", None),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
        }
        if torch.cuda.is_available():
            info["device_0"] = torch.cuda.get_device_name(0)
            info["device_0_capability"] = list(torch.cuda.get_device_capability(0))
            try:
                torch.empty((1,), device="cuda")
                info["tiny_cuda_allocation"] = "ok"
            except Exception as exc:  # noqa: BLE001
                info["tiny_cuda_allocation"] = f"failed: {type(exc).__name__}: {exc}"
        return info
    except Exception as exc:  # noqa: BLE001
        return {"import_ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def repo_status(repo_root: Path | None) -> Dict[str, Any]:
    if repo_root is None:
        return {"provided": False}
    result: Dict[str, Any] = {"provided": True, "exists": repo_root.exists(), "files": {}}
    if repo_root.exists():
        for rel in REPO_FILES:
            result["files"][rel] = (repo_root / rel).exists()
    return result


def path_status(path: Path | None) -> Dict[str, Any]:
    if path is None:
        return {"provided": False}
    return {"provided": True, "exists": path.exists(), "is_file": path.is_file(), "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None}


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Make-It-3D environment and asset diagnostic")
    parser.add_argument("--repo-root", type=Path, default=None, help="Path to the user's Make-It-3D checkout to inspect for expected files")
    parser.add_argument("--dpt-weights", type=Path, default=None, help="Path to dpt_hybrid-midas-501f0c75.pt or another DPT weight file")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when required core modules, CUDA, repo files, or supplied DPT weights are missing")
    args = parser.parse_args(argv)

    module_results = []
    for name, area, required in MODULES:
        item = import_status(name)
        item["area"] = area
        item["required_for_default_check"] = required
        module_results.append(item)

    report: Dict[str, Any] = {
        "schema": "make-it-3d-env-check.v1",
        "python": sys.version.split()[0],
        "executable_basename": Path(sys.executable).name,
        "torch": torch_status(),
        "nvcc_on_path": shutil.which("nvcc") is not None,
        "huggingface_token_present": bool(os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")),
        "modules": module_results,
        "repo": repo_status(args.repo_root),
        "dpt_weights": path_status(args.dpt_weights),
    }

    failures = []
    if not report["torch"].get("cuda_available"):
        failures.append("torch CUDA is not available")
    for item in module_results:
        if item["required_for_default_check"] and not item["ok"]:
            failures.append(f"missing {item['module']} for {item['area']}")
    if args.repo_root and not all(report["repo"].get("files", {}).values()):
        missing = [k for k, v in report["repo"].get("files", {}).items() if not v]
        failures.append("missing repo files: " + ", ".join(missing))
    if args.dpt_weights and not report["dpt_weights"].get("exists"):
        failures.append("supplied DPT weights path does not exist")
    report["strict_failures"] = failures

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Make-It-3D environment diagnostic")
        print(f"Python: {report['python']}")
        print(f"Torch CUDA: {report['torch'].get('cuda_available')} ({report['torch'].get('version')}, cuda {report['torch'].get('cuda_version')})")
        if report["torch"].get("device_0"):
            print(f"GPU 0: {report['torch']['device_0']} capability {report['torch']['device_0_capability']}")
        print(f"nvcc on PATH: {report['nvcc_on_path']}")
        print(f"Hugging Face token env present: {report['huggingface_token_present']}")
        print("\nModules:")
        for item in module_results:
            mark = "OK" if item["ok"] else "MISSING"
            suffix = f" ({item.get('version')})" if item.get("version") else ""
            print(f"  {mark:7} {item['module']:<18} {item['area']}{suffix}")
        if args.repo_root:
            print("\nRepo files:")
            for rel, exists in report["repo"].get("files", {}).items():
                print(f"  {'OK' if exists else 'MISSING':7} {rel}")
        if args.dpt_weights:
            print(f"\nDPT weights: {'OK' if report['dpt_weights'].get('exists') else 'MISSING'} {args.dpt_weights}")
        if failures:
            print("\nStrict failures:")
            for failure in failures:
                print(f"  - {failure}")
    return 1 if args.strict and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
