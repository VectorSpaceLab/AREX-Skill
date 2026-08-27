#!/usr/bin/env python3
"""Check a Detectron2 runtime environment without running models or downloads.

This diagnostic imports core modules, prints package/backend availability, and
inspects a few public API signatures. It does not build models, load weights,
open datasets, download checkpoints, or run training/export.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata
from typing import Any


CORE_IMPORTS = [
    "detectron2",
    "detectron2.config",
    "detectron2.data",
    "detectron2.engine",
    "detectron2.model_zoo",
    "detectron2.structures",
    "detectron2.export",
    "detectron2.evaluation",
    "detectron2.checkpoint",
]

OPTIONAL_IMPORTS = ["cv2", "onnx", "caffe2"]


def import_status(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"name": name, "ok": True, "version": version}


def signature_status(label: str, target: Any) -> dict[str, str]:
    try:
        signature = str(inspect.signature(target))
    except Exception as exc:  # pragma: no cover - diagnostic path
        signature = f"<unavailable: {type(exc).__name__}: {exc}>"
    return {"name": label, "signature": signature}


def collect_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "core_imports": [import_status(name) for name in CORE_IMPORTS],
        "optional_imports": [import_status(name) for name in OPTIONAL_IMPORTS],
        "packages": {},
        "torch": {},
        "signatures": [],
    }

    for package in ["detectron2", "torch", "torchvision", "opencv-python", "opencv-python-headless", "pycocotools"]:
        try:
            report["packages"][package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            report["packages"][package] = None

    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        report["torch"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    else:
        torch_info: dict[str, Any] = {
            "ok": True,
            "version": torch.__version__,
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            try:
                torch_info["cuda_device_0"] = torch.cuda.get_device_name(0)
                torch_info["cuda_capability_0"] = torch.cuda.get_device_capability(0)
            except Exception as exc:  # pragma: no cover - diagnostic path
                torch_info["cuda_device_error"] = f"{type(exc).__name__}: {exc}"
        report["torch"] = torch_info

    if all(item["ok"] for item in report["core_imports"][:6]):
        try:
            from detectron2.config import LazyConfig, get_cfg, instantiate
            from detectron2.data import DatasetCatalog, MetadataCatalog
            from detectron2.engine import DefaultPredictor, DefaultTrainer, launch
            from detectron2.evaluation import COCOEvaluator, inference_on_dataset
            from detectron2.export import TracingAdapter, scripting_with_instances
            from detectron2.model_zoo import get_checkpoint_url, get_config, get_config_file
            from detectron2.structures import Boxes, Instances

            report["signatures"] = [
                signature_status("get_cfg", get_cfg),
                signature_status("LazyConfig.load", LazyConfig.load),
                signature_status("instantiate", instantiate),
                signature_status("DatasetCatalog.register", DatasetCatalog.register),
                signature_status("MetadataCatalog.get", MetadataCatalog.get),
                signature_status("DefaultTrainer", DefaultTrainer),
                signature_status("DefaultPredictor", DefaultPredictor),
                signature_status("launch", launch),
                signature_status("COCOEvaluator", COCOEvaluator),
                signature_status("inference_on_dataset", inference_on_dataset),
                signature_status("get_config_file", get_config_file),
                signature_status("get_checkpoint_url", get_checkpoint_url),
                signature_status("get_config", get_config),
                signature_status("Boxes", Boxes),
                signature_status("Instances", Instances),
                signature_status("TracingAdapter", TracingAdapter),
                signature_status("scripting_with_instances", scripting_with_instances),
            ]
        except Exception as exc:  # pragma: no cover - diagnostic path
            report["signature_error"] = f"{type(exc).__name__}: {exc}"

    return report


def print_text(report: dict[str, Any]) -> None:
    print(f"Python: {report['python']}")
    print("\nCore imports:")
    for item in report["core_imports"]:
        status = "OK" if item["ok"] else "FAIL"
        extra = f" ({item.get('version')})" if item.get("version") else ""
        error = f" - {item.get('error')}" if not item["ok"] else ""
        print(f"- {status} {item['name']}{extra}{error}")
    print("\nOptional imports:")
    for item in report["optional_imports"]:
        status = "OK" if item["ok"] else "missing"
        extra = f" ({item.get('version')})" if item.get("version") else ""
        error = f" - {item.get('error')}" if not item["ok"] else ""
        print(f"- {status} {item['name']}{extra}{error}")
    print("\nPackages:")
    for name, version in report["packages"].items():
        print(f"- {name}: {version or 'not installed'}")
    print("\nTorch:")
    for key, value in report["torch"].items():
        print(f"- {key}: {value}")
    if report.get("signatures"):
        print("\nSelected API signatures:")
        for item in report["signatures"]:
            print(f"- {item['name']}: {item['signature']}")
    if report.get("signature_error"):
        print(f"\nSignature inspection error: {report['signature_error']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Detectron2 import, backend, and API-signature availability.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = collect_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    core_ok = all(item["ok"] for item in report["core_imports"])
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
