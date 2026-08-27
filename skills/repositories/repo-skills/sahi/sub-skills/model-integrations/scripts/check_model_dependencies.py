#!/usr/bin/env python3
"""Safely inspect optional dependency visibility for SAHI model wrappers.

The checker uses importlib.util.find_spec and importlib.metadata only. It does
not import detector frameworks, download model weights, read credentials, train,
or write files.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import metadata
from importlib.util import find_spec

PACKAGE_INFO = {
    "torch": {
        "module": "torch",
        "distribution": "torch",
        "warning": "Required by most model wrappers and by explicit cuda/mps device selection. Install a CPU/CUDA/MPS build that matches the target hardware.",
    },
    "torchvision": {
        "module": "torchvision",
        "distribution": "torchvision",
        "warning": "Must match the installed torch build. Needed by the TorchVision wrapper and sometimes by accelerated postprocess paths.",
    },
    "ultralytics": {
        "module": "ultralytics",
        "distribution": "ultralytics",
        "warning": "Needed for Ultralytics YOLO aliases, YOLOE, YOLO-World, and SAHI's RT-DETR wrapper. A model name may still require local cached weights or a download.",
    },
    "yolov5": {
        "module": "yolov5",
        "distribution": "yolov5",
        "warning": "Needed only for the classic YOLOv5 wrapper; that wrapper also requires torch.",
    },
    "transformers": {
        "module": "transformers",
        "distribution": "transformers",
        "warning": "Needed for HuggingFace detection, GroundingDINO, and HuggingFace segmentation. GroundingDINO requires a new enough Transformers release and text labels or a prompt.",
    },
    "timm": {
        "module": "timm",
        "distribution": "timm",
        "warning": "Not every HuggingFace checkpoint needs timm, but many vision backbones do. Treat a missing timm as checkpoint-dependent.",
    },
    "mmdet": {
        "module": "mmdet",
        "distribution": "mmdet",
        "warning": "MMDetection must be installed with compatible torch, mmcv, and mmengine versions; do not mix these independently.",
    },
    "mmcv": {
        "module": "mmcv",
        "distribution": "mmcv",
        "warning": "Part of the OpenMMLab stack. Its build must match torch/CUDA and the mmdet/mmengine versions.",
    },
    "mmengine": {
        "module": "mmengine",
        "distribution": "mmengine",
        "warning": "Part of the OpenMMLab stack required by the SAHI MMDetection wrapper at module import time.",
    },
    "detectron2": {
        "module": "detectron2",
        "distribution": "detectron2",
        "warning": "Detectron2 wheels/builds are platform, Python, torch, and CUDA sensitive. Importability is not proof that a model-zoo config can run.",
    },
    "inference": {
        "module": "inference",
        "distribution": "inference",
        "warning": "Needed for Roboflow Universe hosted model ids. Hosted ids still require a valid API key at runtime.",
    },
    "rfdetr": {
        "module": "rfdetr",
        "distribution": "rfdetr",
        "warning": "Needed for local RF-DETR classes through the Roboflow wrapper. Custom weights usually require category_mapping and matching resolution.",
    },
    "onnx": {
        "module": "onnx",
        "distribution": "onnx",
        "warning": "Useful for exported ONNX workflows, but runtime execution usually depends on onnxruntime or a provider-specific runtime.",
    },
    "onnxruntime": {
        "module": "onnxruntime",
        "distribution": "onnxruntime",
        "warning": "Needed by many exported ONNX models. Provider availability still depends on the installed runtime build.",
    },
    "numba": {
        "module": "numba",
        "distribution": "numba",
        "warning": "Not a model loader dependency. It affects optional postprocess acceleration; route backend decisions to postprocess guidance.",
    },
    "supervision": {
        "module": "supervision",
        "distribution": "supervision",
        "warning": "Used by local RF-DETR conversion in the Roboflow wrapper and often installed transitively with rfdetr.",
    },
}

MODEL_TYPES = [
    {
        "model_type": "ultralytics",
        "normalized_to": "ultralytics",
        "required": ["ultralytics"],
        "optional": ["onnx", "onnxruntime"],
        "note": "Ultralytics YOLO detection/segmentation/OBB; aliases yolov8/yolov11/yolo11/yolo26 normalize here.",
    },
    {
        "model_type": "yolov8",
        "normalized_to": "ultralytics",
        "required": ["ultralytics"],
        "optional": ["onnx", "onnxruntime"],
        "note": "AutoDetectionModel alias for the Ultralytics wrapper.",
    },
    {
        "model_type": "yolov11",
        "normalized_to": "ultralytics",
        "required": ["ultralytics"],
        "optional": ["onnx", "onnxruntime"],
        "note": "AutoDetectionModel alias for the Ultralytics wrapper.",
    },
    {
        "model_type": "yolo11",
        "normalized_to": "ultralytics",
        "required": ["ultralytics"],
        "optional": ["onnx", "onnxruntime"],
        "note": "AutoDetectionModel alias for the Ultralytics wrapper.",
    },
    {
        "model_type": "yolo26",
        "normalized_to": "ultralytics",
        "required": ["ultralytics"],
        "optional": ["onnx", "onnxruntime"],
        "note": "AutoDetectionModel alias for the Ultralytics wrapper.",
    },
    {
        "model_type": "yoloe",
        "normalized_to": "yoloe",
        "required": ["ultralytics"],
        "optional": [],
        "note": "YOLOE open-vocabulary/prompt-free route via Ultralytics.",
    },
    {
        "model_type": "yolo-world",
        "normalized_to": "yolo-world",
        "required": ["ultralytics"],
        "optional": [],
        "note": "YOLO-World route via Ultralytics. If AutoDetectionModel raises a class-name AttributeError, check the installed SAHI auto-map.",
    },
    {
        "model_type": "yolov5",
        "normalized_to": "yolov5",
        "required": ["yolov5", "torch"],
        "optional": [],
        "note": "Classic YOLOv5 wrapper.",
    },
    {
        "model_type": "rtdetr",
        "normalized_to": "rtdetr",
        "required": ["ultralytics"],
        "optional": [],
        "note": "SAHI's RT-DETR wrapper uses ultralytics.RTDETR. HuggingFace RT-DETR checkpoints use model_type=huggingface.",
    },
    {
        "model_type": "huggingface",
        "normalized_to": "huggingface",
        "required": ["torch", "transformers"],
        "optional": ["timm"],
        "note": "HuggingFace object detection and GroundingDINO zero-shot detection; token/text labels are runtime concerns.",
    },
    {
        "model_type": "huggingface_segmentation",
        "normalized_to": "huggingface_segmentation",
        "required": ["torch", "transformers"],
        "optional": ["timm"],
        "note": "HuggingFace MaskFormer/Mask2Former/OneFormer segmentation route.",
    },
    {
        "model_type": "hugging_face_universal_segmentation",
        "normalized_to": "hugging_face_universal_segmentation",
        "required": ["torch", "transformers"],
        "optional": ["timm"],
        "note": "Declared in the inspected auto-map, but no matching wrapper class was found there; prefer huggingface_segmentation unless your installed SAHI release verifies this route.",
    },
    {
        "model_type": "torchvision",
        "normalized_to": "torchvision",
        "required": ["torch", "torchvision"],
        "optional": [],
        "note": "TorchVision detection and instance segmentation models.",
    },
    {
        "model_type": "mmdet",
        "normalized_to": "mmdet",
        "required": ["torch", "mmdet", "mmcv", "mmengine"],
        "optional": [],
        "note": "MMDetection/OpenMMLab wrapper. Stack compatibility matters as much as package presence.",
    },
    {
        "model_type": "detectron2",
        "normalized_to": "detectron2",
        "required": ["torch", "detectron2"],
        "optional": [],
        "note": "Detectron2 wrapper; wheel/platform compatibility is a common blocker.",
    },
    {
        "model_type": "roboflow",
        "normalized_to": "roboflow",
        "required": [],
        "route_dependent": ["inference", "rfdetr", "supervision"],
        "optional": [],
        "note": "Route-dependent: Roboflow Universe ids need inference + API key; local RF-DETR needs rfdetr and usually supervision.",
    },
]


def probe_package(package_key):
    info = PACKAGE_INFO[package_key]
    module = info["module"]
    distribution = info.get("distribution") or module
    try:
        importable = find_spec(module) is not None
    except (ImportError, AttributeError, ValueError):
        importable = False

    try:
        version = metadata.version(distribution)
    except metadata.PackageNotFoundError:
        version = "unknown" if importable else None
    except Exception:
        version = "unknown"

    return {
        "key": package_key,
        "module": module,
        "distribution": distribution,
        "importable": importable,
        "version": version,
        "warning": info["warning"],
    }


def evaluate_model(model_spec, probes):
    required = model_spec.get("required", [])
    route_dependent = model_spec.get("route_dependent", [])
    optional = model_spec.get("optional", [])
    missing_required = [pkg for pkg in required if not probes[pkg]["importable"]]

    if missing_required:
        status = "missing-required"
    elif route_dependent:
        present_routes = [pkg for pkg in route_dependent if probes[pkg]["importable"]]
        status = "route-dependent-present" if present_routes else "route-dependent-missing"
    else:
        status = "ok"

    return {
        "model_type": model_spec["model_type"],
        "normalized_to": model_spec["normalized_to"],
        "status": status,
        "required": [probes[pkg] for pkg in required],
        "route_dependent": [probes[pkg] for pkg in route_dependent],
        "optional": [probes[pkg] for pkg in optional],
        "note": model_spec["note"],
    }


def package_summary(probe):
    if probe["importable"]:
        version = probe["version"] or "unknown"
        return f"{probe['key']}=yes ({version})"
    return f"{probe['key']}=no"


def print_text(results, probes, include_warnings):
    print("SAHI optional model dependency check (spec-only; no heavy imports, downloads, or credentials)\n")
    print(f"Python: {sys.version.split()[0]}\n")
    for result in results:
        print(f"[{result['status']}] {result['model_type']} -> {result['normalized_to']}")
        if result["required"]:
            print("  required: " + ", ".join(package_summary(pkg) for pkg in result["required"]))
        if result["route_dependent"]:
            print("  route-dependent: " + ", ".join(package_summary(pkg) for pkg in result["route_dependent"]))
        if result["optional"]:
            print("  optional/runtime: " + ", ".join(package_summary(pkg) for pkg in result["optional"]))
        print(f"  note: {result['note']}\n")

    if include_warnings:
        print("Package warnings:")
        for key in sorted(PACKAGE_INFO):
            probe = probes[key]
            state = "present" if probe["importable"] else "missing"
            version = f" {probe['version']}" if probe["version"] else ""
            print(f"- {key} [{state}{version}]: {probe['warning']}")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Safely check which optional packages for SAHI model_type routes appear importable."
    )
    parser.add_argument(
        "--model-type",
        action="append",
        default=[],
        help="Limit output to one or more model_type values, e.g. --model-type ultralytics --model-type mmdet.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--no-warnings", action="store_true", help="Suppress the package warning section in text output.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    known = {item["model_type"]: item for item in MODEL_TYPES}
    if args.model_type:
        unknown = [item for item in args.model_type if item not in known]
        if unknown:
            print("Unknown model_type value(s): " + ", ".join(unknown), file=sys.stderr)
            print("Known values: " + ", ".join(sorted(known)), file=sys.stderr)
            return 2
        selected = [known[item] for item in args.model_type]
    else:
        selected = MODEL_TYPES

    all_package_keys = sorted(PACKAGE_INFO)
    probes = {key: probe_package(key) for key in all_package_keys}
    results = [evaluate_model(item, probes) for item in selected]

    if args.json:
        print(json.dumps({"python": sys.version.split()[0], "results": results, "packages": probes}, indent=2, sort_keys=True))
    else:
        print_text(results, probes, include_warnings=not args.no_warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
