#!/usr/bin/env python3
"""Inspect a YOLOv5 checkout and active Python environment without downloads or training."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

CORE_MODULES = [
    "models.common",
    "models.yolo",
    "utils.general",
    "utils.downloads",
    "utils.dataloaders",
    "hubconf",
    "detect",
    "train",
    "val",
    "export",
    "benchmarks",
    "segment.train",
    "segment.val",
    "segment.predict",
    "classify.train",
    "classify.val",
    "classify.predict",
    "utils.flask_rest_api.restapi",
]
OPTIONAL_PACKAGES = ["ultralytics", "torch", "torchvision", "onnx", "Flask", "pytest"]


def _safe_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _load_module(name: str) -> tuple[bool, str | None]:
    try:
        mod = importlib.import_module(name)
        return True, getattr(mod, "__file__", None)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, f"{type(exc).__name__}: {exc}"


def _cuda_smoke() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"available": False, "error": f"torch import failed: {type(exc).__name__}: {exc}"}

    smoke: dict[str, Any] = {
        "torch_version": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "available": bool(torch.cuda.is_available()),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
    }
    if torch.cuda.is_available():
        try:
            smoke["device_name"] = torch.cuda.get_device_name(0)
            smoke["capability"] = list(torch.cuda.get_device_capability(0))
            tensor = torch.empty((1,), device="cuda")
            smoke["allocation"] = str(tensor.device)
        except Exception as exc:  # pragma: no cover - diagnostic path
            smoke["error"] = f"CUDA smoke failed: {type(exc).__name__}: {exc}"
    return smoke


def build_report(repo_root: Path | None) -> dict[str, Any]:
    if repo_root is not None:
        sys.path.insert(0, str(repo_root))

    imports = {}
    for name in CORE_MODULES:
        ok, detail = _load_module(name)
        imports[name] = {"ok": ok, "detail": detail}

    report = {
        "python": {
            "executable": sys.executable,
            "version": sys.version,
        },
        "distributions": {name: _safe_version(name) for name in OPTIONAL_PACKAGES},
        "imports": imports,
        "cuda": _cuda_smoke(),
        "repo_root": str(repo_root) if repo_root is not None else None,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a YOLOv5 environment without downloads or training")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="YOLOv5 checkout root to add to sys.path")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human-readable output")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve() if args.repo_root else None
    report = build_report(repo_root)

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"Python: {report['python']['version'].split()[0]} @ {report['python']['executable']}")
        for name, value in report["distributions"].items():
            print(f"{name}: {value or 'NOT INSTALLED'}")
        print(f"CUDA available: {report['cuda'].get('available')}")
        if report["cuda"].get("available"):
            print(f"CUDA device count: {report['cuda'].get('device_count')}")
            print(f"CUDA device name: {report['cuda'].get('device_name')}")
            print(f"CUDA capability: {report['cuda'].get('capability')}")
        for name, item in report["imports"].items():
            status = "OK" if item["ok"] else "FAIL"
            print(f"{status} {name}: {item['detail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
