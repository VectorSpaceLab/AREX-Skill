#!/usr/bin/env python3
"""Check optional export dependencies without converting any model."""

from __future__ import annotations

import argparse
import json
from importlib import import_module
from importlib.util import find_spec

FORMAT_MODULES = {
    "torchscript": [],
    "onnx": ["onnx"],
    "openvino": ["openvino"],
    "engine": [],
    "coreml": ["coremltools"],
    "saved_model": ["tensorflow"],
    "pb": ["tensorflow"],
    "tflite": ["tensorflow"],
    "edgetpu": [],
    "tfjs": ["tensorflowjs"],
    "paddle": ["paddle"],
}


def check_packages(formats: list[str]) -> dict[str, object]:
    report: dict[str, object] = {"formats": {}, "notes": []}
    for fmt in formats:
        packages = FORMAT_MODULES.get(fmt)
        if packages is None:
            report["formats"][fmt] = {"known": False, "missing": [], "present": []}
            report["notes"].append(f"unknown format {fmt!r}")
            continue
        present = []
        missing = []
        for package in packages:
            if find_spec(package) is not None:
                present.append(package)
            else:
                missing.append(package)
        report["formats"][fmt] = {"known": True, "missing": missing, "present": present}
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check YOLOv5 export prerequisites without exporting a model")
    parser.add_argument("--formats", nargs="+", default=["torchscript", "onnx"], help="formats to inspect")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args()

    report = check_packages(args.formats)
    report["formats_requested"] = args.formats
    report["python"] = {"executable": __import__("sys").executable}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for fmt, data in report["formats"].items():
            status = "ok" if not data["missing"] else "missing"
            print(f"{fmt}: {status}")
            if data["present"]:
                print(f"  present: {', '.join(data['present'])}")
            if data["missing"]:
                print(f"  missing: {', '.join(data['missing'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
