#!/usr/bin/env python3
"""Read-only Pytorch-Wildlife detection preflight.

This helper imports public modules and inspects signatures only. It never
constructs a detector, opens an image, downloads weights, starts a service, or
writes a cache file. It is deliberately independent of the caller's cwd.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import inspect
import json
import sys
from typing import Any


CLASSES = (
    "MegaDetectorV5",
    "MegaDetectorV6",
    "MegaDetectorV6MIT",
    "MegaDetectorV6Apache",
    "HerdNet",
    "OWLC",
    "OWLT",
    "DeepfauneDetector",
    "MegaDetectorV6_Distributed",
)
METHODS = ("single_image_detection", "batch_image_detection")


def package_version() -> str | None:
    for name in ("PytorchWildlife", "pytorch-wildlife"):
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue
    return None


def signature(value: Any) -> str | None:
    try:
        return str(inspect.signature(value))
    except (TypeError, ValueError):
        return None


def build_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "package_version": package_version(),
        "torch": None,
        "cuda_available": None,
        "detection_import": {"ok": False, "error": None},
        "classes": {},
    }

    try:
        torch = importlib.import_module("torch")
        report["torch"] = getattr(torch, "__version__", "unknown")
        try:
            report["cuda_available"] = bool(torch.cuda.is_available())
        except Exception as exc:  # device probing must not abort diagnostics
            report["cuda_available"] = f"probe-error: {type(exc).__name__}: {exc}"
    except Exception as exc:
        report["torch"] = f"import-error: {type(exc).__name__}: {exc}"

    try:
        detection = importlib.import_module("PytorchWildlife.models.detection")
        report["detection_import"] = {"ok": True, "error": None}
        for name in CLASSES:
            cls = getattr(detection, name, None)
            item: dict[str, Any] = {"available": cls is not None}
            if cls is not None:
                item["constructor"] = signature(cls)
                for method in METHODS:
                    item[method] = signature(getattr(cls, method, None))
            report["classes"][name] = item
    except Exception as exc:
        report["detection_import"] = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
        for name in CLASSES:
            report["classes"][name] = {"available": False}

    return report


def print_human(report: dict[str, Any]) -> None:
    print(f"Python: {report['python']}")
    print(f"PytorchWildlife distribution: {report['package_version'] or 'not found'}")
    print(f"Torch: {report['torch'] or 'not found'}")
    print(f"CUDA available: {report['cuda_available']}")
    imported = report["detection_import"]
    print(f"Detection module import: {'ok' if imported['ok'] else 'FAILED'}")
    if imported["error"]:
        print(f"  import error: {imported['error']}")
    for name, item in report["classes"].items():
        if not item["available"]:
            print(f"{name}: unavailable")
            continue
        print(f"{name}: {item['constructor']}")
        print(f"  single: {item['single_image_detection']}")
        print(f"  batch:  {item['batch_image_detection']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return non-zero when the detection module or required classes are unavailable",
    )
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    if not args.strict:
        return 0
    required = report["detection_import"]["ok"] and all(
        report["classes"][name]["available"] for name in CLASSES[:-1]
    )
    return 0 if required else 1


if __name__ == "__main__":
    raise SystemExit(main())
