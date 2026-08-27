#!/usr/bin/env python3
"""Check ImageAI 3.x imports, key APIs, and optional CUDA availability.

This diagnostic is safe: it does not download weights, open cameras, read user
images/videos, or start training. It only imports packages, constructs key
classes, and inspects signatures.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke-check ImageAI 3.x environment and key APIs.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if torch CUDA is unavailable or a tiny CUDA allocation fails.")
    parser.add_argument("--quiet", action="store_true", help="Print compact JSON only.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report: dict[str, Any] = {"ok": False, "python": sys.version.split()[0], "imports": {}, "signatures": {}, "errors": []}

    try:
        import torch
        import torchvision
        report["imports"]["torch"] = getattr(torch, "__version__", "unknown")
        report["imports"]["torchvision"] = getattr(torchvision, "__version__", "unknown")
        report["cuda"] = {
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
            "torch_cuda_version": getattr(torch.version, "cuda", None),
        }
        if torch.cuda.is_available():
            report["cuda"].update(
                {
                    "device_name_0": torch.cuda.get_device_name(0),
                    "device_capability_0": list(torch.cuda.get_device_capability(0)),
                }
            )
            try:
                torch.empty((1,), device="cuda")
                report["cuda"]["tiny_allocation"] = "passed"
            except Exception as exc:  # pragma: no cover - hardware-specific
                report["cuda"]["tiny_allocation"] = "failed"
                report["errors"].append({"where": "cuda_allocation", "error": str(exc)})
    except Exception as exc:
        report["errors"].append({"where": "torch_import", "error": str(exc), "type": type(exc).__name__})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    try:
        import imageai
        from importlib.metadata import version
        from imageai.Classification import ImageClassification
        from imageai.Classification.Custom import ClassificationModelTrainer, CustomImageClassification
        from imageai.Detection import ObjectDetection, VideoObjectDetection
        from imageai.Detection.Custom import DetectionModelTrainer, CustomObjectDetection, CustomVideoObjectDetection

        report["imports"]["imageai"] = version("imageai")
        classes = [
            ImageClassification,
            ClassificationModelTrainer,
            CustomImageClassification,
            ObjectDetection,
            VideoObjectDetection,
            DetectionModelTrainer,
            CustomObjectDetection,
            CustomVideoObjectDetection,
        ]
        constructed: list[str] = []
        for cls in classes:
            cls()
            constructed.append(cls.__name__)
        report["constructed_classes"] = constructed
        targets = {
            "ImageClassification.classifyImage": ImageClassification.classifyImage,
            "CustomImageClassification.classifyImage": CustomImageClassification.classifyImage,
            "ClassificationModelTrainer.trainModel": ClassificationModelTrainer.trainModel,
            "ObjectDetection.detectObjectsFromImage": ObjectDetection.detectObjectsFromImage,
            "VideoObjectDetection.detectObjectsFromVideo": VideoObjectDetection.detectObjectsFromVideo,
            "DetectionModelTrainer.setTrainConfig": DetectionModelTrainer.setTrainConfig,
            "CustomObjectDetection.detectObjectsFromImage": CustomObjectDetection.detectObjectsFromImage,
            "CustomVideoObjectDetection.detectObjectsFromVideo": CustomVideoObjectDetection.detectObjectsFromVideo,
        }
        for name, func in targets.items():
            report["signatures"][name] = str(inspect.signature(func))
    except Exception as exc:
        report["errors"].append({"where": "imageai_import_or_api", "error": str(exc), "type": type(exc).__name__})

    if args.require_cuda and not report.get("cuda", {}).get("available"):
        report["errors"].append({"where": "cuda_required", "error": "--require-cuda was set but torch.cuda.is_available() is false"})
    if args.require_cuda and report.get("cuda", {}).get("tiny_allocation") == "failed":
        report["errors"].append({"where": "cuda_required", "error": "CUDA tiny tensor allocation failed"})

    report["ok"] = not report["errors"]
    if not args.quiet and not report["ok"]:
        print("ImageAI environment check failed; see JSON details below.", file=sys.stderr)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
