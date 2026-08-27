#!/usr/bin/env python3
"""Check a Neuralangelo runtime without assuming a private checkout path.

This script is intentionally read-only. It can be run from any directory and can
optionally add a user-provided Neuralangelo project root to sys.path before
checking imports.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any


DISTRIBUTIONS = [
    "torch",
    "torchvision",
    "tinycudann",
    "tiny-cuda-nn",
    "numpy",
    "PyYAML",
    "addict",
    "opencv-python-headless",
    "trimesh",
    "PyMCubes",
    "wandb",
]

IMPORTS = [
    ("torch", "torch"),
    ("torchvision", "torchvision"),
    ("tinycudann", "tinycudann"),
    ("imaginaire.config.Config", "imaginaire.config"),
    ("projects.neuralangelo.model.Model", "projects.neuralangelo.model"),
    ("projects.neuralangelo.data.Dataset", "projects.neuralangelo.data"),
    ("projects.neuralangelo.trainer.Trainer", "projects.neuralangelo.trainer"),
]


def version_for(dist: str) -> str | None:
    try:
        return importlib.metadata.version(dist)
    except importlib.metadata.PackageNotFoundError:
        return None


def try_import(label: str, module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
        return {"label": label, "module": module, "ok": True, "file": getattr(imported, "__file__", None)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"label": label, "module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def nvidia_smi() -> dict[str, Any]:
    exe = "nvidia-smi"
    try:
        proc = subprocess.run(
            [exe, "--query-gpu=name,memory.total,driver_version,compute_cap", "--format=csv,noheader,nounits"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - host dependent
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    rows = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return {"ok": proc.returncode == 0, "returncode": proc.returncode, "rows": rows, "stderr": proc.stderr.strip()}


def torch_cuda_probe() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "torch_imported": False, "error": f"{type(exc).__name__}: {exc}"}

    result: dict[str, Any] = {
        "torch_imported": True,
        "torch_version": getattr(torch, "__version__", None),
        "cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        "devices": [],
    }
    if torch.cuda.is_available():
        for idx in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(idx)
            result["devices"].append(
                {
                    "index": idx,
                    "name": props.name,
                    "total_memory_gb": round(props.total_memory / (1024**3), 2),
                    "capability": f"{props.major}.{props.minor}",
                }
            )
        try:
            tensor = torch.empty((1,), device="cuda")
            tensor += 1
            torch.cuda.synchronize()
            result["cuda_allocation_ok"] = True
        except Exception as exc:  # pragma: no cover - host dependent
            result["cuda_allocation_ok"] = False
            result["cuda_allocation_error"] = f"{type(exc).__name__}: {exc}"
    result["ok"] = bool(result.get("cuda_available") and result.get("cuda_allocation_ok", False))
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a Neuralangelo CUDA/runtime environment.")
    parser.add_argument("--project-root", help="Target Neuralangelo project root to add to sys.path for source-tree imports.")
    parser.add_argument("--require-cuda", action="store_true", help="Exit nonzero unless CUDA import/allocation checks pass.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(args.project_root).expanduser().resolve() if args.project_root else None
    root_status: dict[str, Any]
    if project_root:
        root_status = {"path": str(project_root), "exists": project_root.exists(), "is_dir": project_root.is_dir()}
        if project_root.is_dir():
            sys.path.insert(0, str(project_root))
            os.chdir(project_root)
    else:
        root_status = {"path": None, "note": "No project root supplied; imports use the current Python environment."}

    imports = [try_import(label, module) for label, module in IMPORTS]
    cuda = torch_cuda_probe()
    report = {
        "python": {"executable": sys.executable, "version": sys.version.split()[0], "platform": platform.platform()},
        "project_root": root_status,
        "distributions": {dist: version_for(dist) for dist in DISTRIBUTIONS},
        "imports": imports,
        "cuda": cuda,
        "nvidia_smi": nvidia_smi(),
    }
    report["ok"] = all(item["ok"] for item in imports) and (cuda["ok"] if args.require_cuda else True)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']['version']} ({report['python']['executable']})")
        if project_root:
            print(f"Project root: {project_root} exists={root_status['exists']}")
        for item in imports:
            status = "ok" if item["ok"] else "FAIL"
            print(f"import {item['label']}: {status}")
            if not item["ok"]:
                print(f"  {item['error']}")
        print(f"CUDA available: {cuda.get('cuda_available')} allocation_ok={cuda.get('cuda_allocation_ok')}")
        for dev in cuda.get("devices", []):
            print(f"  GPU {dev['index']}: {dev['name']} {dev['total_memory_gb']} GB cc {dev['capability']}")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
