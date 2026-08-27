#!/usr/bin/env python3
"""Report which face detector backends are available.

Purpose: provide a safe backend-availability probe without downloading model
weights. The script reports importability and optional dependency status for the
supported detector backends.

Prerequisites: install `face-alignment` into the active environment.

Example:
    python scripts/check_detector_support.py
"""
from __future__ import annotations

from importlib import import_module
import sys


def _status(ok: bool) -> str:
    return "ok" if ok else "missing"


def main() -> int:
    try:
        import face_alignment
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"face_alignment import failed: {exc}", file=sys.stderr)
        return 1

    backends = [
        {
            "name": "sfd",
            "module": "face_alignment.detection.sfd",
            "optional_dep": None,
            "note": "default PyTorch backend",
        },
        {
            "name": "blazeface",
            "module": "face_alignment.detection.blazeface",
            "optional_dep": None,
            "note": "speed-oriented PyTorch backend",
        },
        {
            "name": "yunet",
            "module": "face_alignment.detection.yunet",
            "optional_dep": None,
            "note": "OpenCV CPU backend",
        },
        {
            "name": "retinaface",
            "module": "face_alignment.detection.retinaface",
            "optional_dep": "torchvision",
            "note": "PyTorch backend that needs torchvision",
        },
        {
            "name": "scrfd",
            "module": "face_alignment.detection.scrfd",
            "optional_dep": "onnxruntime",
            "note": "ONNX Runtime backend that needs the optional extra",
        },
        {
            "name": "folder",
            "module": "face_alignment.detection.folder",
            "optional_dep": None,
            "note": "precomputed sidecar boxes",
        },
        {
            "name": "dlib",
            "module": "face_alignment.detection.dlib",
            "optional_dep": "dlib",
            "note": "deprecated legacy backend",
        },
    ]

    print(f"face_alignment: {face_alignment.__version__}")
    print("backend       module import   optional dep   availability   note")
    print("-" * 72)
    for backend in backends:
        module_ok = True
        dep_ok = True
        module_error = ""
        dep_error = ""

        try:
            import_module(backend["module"])
        except Exception as exc:
            module_ok = False
            module_error = f"{exc.__class__.__name__}: {exc}"

        optional_dep = backend["optional_dep"]
        if optional_dep is not None:
            try:
                import_module(optional_dep)
            except Exception as exc:
                dep_ok = False
                dep_error = f"{exc.__class__.__name__}: {exc}"

        available = module_ok and dep_ok
        print(
            f"{backend['name']:<12} {_status(module_ok):<14} "
            f"{_status(dep_ok) if optional_dep else 'n/a':<13} "
            f"{_status(available):<13} {backend['note']}"
        )
        if module_error:
            print(f"  module error: {module_error}")
        if dep_error:
            print(f"  optional dep error: {dep_error}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
