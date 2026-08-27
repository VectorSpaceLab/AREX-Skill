#!/usr/bin/env python3
"""Preflight HDR EXR export requirements for ComfyUI-LTXVideo.

This helper checks environment and optional OpenCV capabilities without importing
ComfyUI, loading models, or writing EXR files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


def _opencv_probe() -> dict[str, Any]:
    probe: dict[str, Any] = {
        "imported": False,
        "version": None,
        "error": None,
        "exr_constants": {},
        "have_image_writer_exr": None,
        "build_mentions_openexr": None,
    }
    try:
        import cv2  # type: ignore[import-not-found]
    except Exception as exc:  # ImportError or binary-load errors.
        probe["error"] = f"{type(exc).__name__}: {exc}"
        return probe

    probe["imported"] = True
    probe["version"] = getattr(cv2, "__version__", None)

    for name in (
        "IMWRITE_EXR_TYPE",
        "IMWRITE_EXR_TYPE_HALF",
        "IMWRITE_EXR_TYPE_FLOAT",
        "IMWRITE_EXR_COMPRESSION",
        "IMWRITE_EXR_COMPRESSION_ZIP",
    ):
        probe["exr_constants"][name] = hasattr(cv2, name)

    try:
        probe["have_image_writer_exr"] = bool(cv2.haveImageWriter(".exr"))
    except Exception as exc:
        probe["have_image_writer_exr"] = f"error: {type(exc).__name__}: {exc}"

    try:
        info = cv2.getBuildInformation()
        probe["build_mentions_openexr"] = "OpenEXR" in info or "openexr" in info.lower()
    except Exception as exc:
        probe["build_mentions_openexr"] = f"error: {type(exc).__name__}: {exc}"

    return probe


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check OPENCV_IO_ENABLE_OPENEXR and optional cv2 EXR support without writing files."
    )
    parser.add_argument(
        "--skip-cv2",
        action="store_true",
        help="only check OPENCV_IO_ENABLE_OPENEXR; do not attempt to import cv2",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero unless the env var is set, cv2 imports, and EXR constants are present",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    env_value = os.environ.get("OPENCV_IO_ENABLE_OPENEXR")
    env_ok = env_value == "1"
    warnings: list[str] = []
    errors: list[str] = []

    if not env_ok:
        msg = (
            "OPENCV_IO_ENABLE_OPENEXR is not set to '1'. Set it in the process "
            "environment before starting ComfyUI and before cv2 imports if save_exr will be enabled."
        )
        (errors if args.strict else warnings).append(msg)

    cv2_probe = None
    if not args.skip_cv2:
        cv2_probe = _opencv_probe()
        if not cv2_probe["imported"]:
            msg = "cv2 could not be imported; install optional opencv-python support before enabling EXR output."
            (errors if args.strict else warnings).append(msg)
        else:
            missing = [
                name
                for name, present in cv2_probe["exr_constants"].items()
                if not present
            ]
            if missing:
                msg = "cv2 imported but is missing EXR constants: " + ", ".join(missing)
                (errors if args.strict else warnings).append(msg)
            if cv2_probe["have_image_writer_exr"] is False:
                msg = "cv2.haveImageWriter('.exr') returned false; this OpenCV build may not write EXR."
                (errors if args.strict else warnings).append(msg)

    result = {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "warnings": warnings,
        "environment": {
            "OPENCV_IO_ENABLE_OPENEXR": env_value,
            "openexr_env_ready_before_cv2_import": env_ok,
        },
        "cv2": cv2_probe,
        "writes_files": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
