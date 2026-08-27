#!/usr/bin/env python3
"""Quick install and import check for face-alignment.

Purpose: confirm the installed `face_alignment` package imports, report the
public constructor signature, and show whether the optional backend modules are
available.

Prerequisites: run after installing the package into the intended environment.

Example:
    python scripts/check_install.py
"""
from __future__ import annotations

from importlib import metadata
from inspect import signature
import sys


def _version(dist_name: str) -> str:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return "missing"


def main() -> int:
    try:
        import face_alignment
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"face_alignment import failed: {exc}", file=sys.stderr)
        return 1

    lines = []
    lines.append(f"face_alignment: {face_alignment.__version__}")
    lines.append(f"module: {face_alignment.__file__}")
    lines.append(f"FaceAlignment: {signature(face_alignment.FaceAlignment)}")
    lines.append(
        "LandmarksType: "
        + ", ".join(name for name in face_alignment.LandmarksType.__members__)
    )

    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        lines.append(f"torch: missing ({exc})")
    else:
        lines.append(f"torch: {torch.__version__} | cuda={torch.version.cuda} | available={torch.cuda.is_available()}")
        if torch.cuda.is_available():
            lines.append(f"cuda device: {torch.cuda.get_device_name(0)} | capability={torch.cuda.get_device_capability(0)}")

    for dist_name in ["torchvision", "onnxruntime", "numba", "scikit-image", "opencv-python"]:
        lines.append(f"{dist_name}: {_version(dist_name)}")

    for mod_name in [
        "face_alignment.detection.retinaface",
        "face_alignment.detection.scrfd",
        "dlib",
    ]:
        try:
            __import__(mod_name)
        except Exception as exc:
            lines.append(f"{mod_name}: missing optional dependency ({exc.__class__.__name__}: {exc})")
        else:
            lines.append(f"{mod_name}: ok")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
