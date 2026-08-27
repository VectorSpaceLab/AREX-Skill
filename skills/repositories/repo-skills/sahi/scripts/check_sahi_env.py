#!/usr/bin/env python3
"""Check a SAHI runtime without downloading models or requiring credentials.

Examples:
    python scripts/check_sahi_env.py
    python scripts/check_sahi_env.py --json --require sahi numpy opencv-python
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import json
import sys
from typing import Any

OPTIONAL_MODULES = {
    "torch": "torch device utilities, YOLOv5, TorchVision, HuggingFace, MMDetection, Detectron2",
    "torchvision": "TorchVision model wrapper and GPU/MPS postprocess backend",
    "ultralytics": "Ultralytics YOLO, YOLOE, YOLO-World, RT-DETR route",
    "yolov5": "classic YOLOv5 route",
    "transformers": "HuggingFace detection, GroundingDINO, segmentation route",
    "timm": "common HuggingFace vision model dependency",
    "mmdet": "MMDetection wrapper",
    "mmcv": "OpenMMLab/MMDetection stack",
    "mmengine": "OpenMMLab/MMDetection stack",
    "detectron2": "Detectron2 wrapper",
    "inference": "Roboflow Universe hosted model ids",
    "rfdetr": "local RF-DETR model route",
    "onnx": "ONNX export/model workflows",
    "onnxruntime": "ONNX runtime workflows",
    "numba": "numba postprocess backend",
    "pycocotools": "COCO evaluation and error analysis",
    "fiftyone": "interactive dataset/result visualization",
    "imantics": "optional annotation conversion",
}

DISTRIBUTION_TO_MODULE = {
    "opencv-python": "cv2",
    "pillow": "PIL",
    "pyyaml": "yaml",
}


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def check_distribution(name: str) -> dict[str, Any]:
    module = DISTRIBUTION_TO_MODULE.get(name, name.replace("-", "_"))
    return {
        "distribution": name,
        "version": dist_version(name),
        "module": module,
        "module_available": module_available(module),
    }


def collect() -> dict[str, Any]:
    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "required": {},
        "optional_modules": {},
        "sahi": {},
        "postprocess_backend": {},
        "warnings": [],
    }

    for dist in ["sahi", "numpy", "opencv-python", "pillow", "shapely", "matplotlib", "pyyaml", "fire", "requests", "click", "tqdm"]:
        result["required"][dist] = check_distribution(dist)

    try:
        import sahi
        from sahi.postprocess.backends import get_postprocess_backend, resolve_backend
        from sahi.utils.import_utils import get_opencv_conflict_message

        result["sahi"] = {
            "imported": True,
            "version": getattr(sahi, "__version__", None),
            "public_symbols": sorted(getattr(sahi, "__all__", [])),
        }
        result["postprocess_backend"] = {
            "configured": get_postprocess_backend(),
            "resolved": resolve_backend(),
        }
        conflict = get_opencv_conflict_message()
        if conflict:
            result["warnings"].append(conflict)
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["sahi"] = {"imported": False, "error": f"{type(exc).__name__}: {exc}"}

    for module, purpose in OPTIONAL_MODULES.items():
        dist_name = module
        if module == "PIL":
            dist_name = "pillow"
        result["optional_modules"][module] = {
            "available": module_available(module),
            "version": dist_version(dist_name),
            "purpose": purpose,
        }

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check installed SAHI package and optional dependency visibility.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument(
        "--require",
        nargs="*",
        default=[],
        help="Distribution names that must have metadata and importable modules, e.g. sahi numpy opencv-python.",
    )
    args = parser.parse_args()

    data = collect()
    failures: list[str] = []
    for dist in args.require:
        entry = check_distribution(dist)
        if not entry["version"] or not entry["module_available"]:
            failures.append(f"{dist}: version={entry['version']!r}, module_available={entry['module_available']}")

    if args.json:
        payload = dict(data)
        payload["required_failures"] = failures
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Python: {data['python']}")
        sahi = data["sahi"]
        if sahi.get("imported"):
            print(f"SAHI: imported version={sahi.get('version')}")
        else:
            print(f"SAHI: FAILED {sahi.get('error')}")
        backend = data.get("postprocess_backend", {})
        if backend:
            print(f"Postprocess backend: configured={backend.get('configured')} resolved={backend.get('resolved')}")
        print("\nRequired/base distributions:")
        for dist, entry in data["required"].items():
            status = "ok" if entry["version"] and entry["module_available"] else "missing"
            print(f"- {dist}: {status} version={entry['version']} module={entry['module']} importable={entry['module_available']}")
        print("\nOptional modules:")
        for module, entry in data["optional_modules"].items():
            status = "yes" if entry["available"] else "no"
            print(f"- {module}: {status} version={entry['version']} — {entry['purpose']}")
        for warning in data["warnings"]:
            print(f"WARNING: {warning}")
        if failures:
            print("\nRequired failures:")
            for failure in failures:
                print(f"- {failure}")

    return 1 if failures or not data.get("sahi", {}).get("imported") else 0


if __name__ == "__main__":
    raise SystemExit(main())
