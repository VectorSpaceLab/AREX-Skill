#!/usr/bin/env python3
"""Check a SimpleITK Python environment without source data or network access.

The script imports SimpleITK, creates tiny synthetic images, exercises NumPy
conversion when NumPy is available, lists registered ImageIO backends through
reader/writer object APIs, checks registration/resampling availability, and
reports optional elastix/transformix wrapper presence.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print JSON diagnostics for an installed SimpleITK environment."
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument(
        "--skip-numpy",
        action="store_true",
        help="Skip NumPy bridge checks even if NumPy is installed.",
    )
    return parser.parse_args(argv)


def import_simpleitk() -> Any:
    try:
        import SimpleITK as sitk  # type: ignore
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "stage": "import",
                    "error": str(exc),
                    "hint": "Install with `python -m pip install simpleitk` or use a conda-forge environment containing `simpleitk`.",
                },
                sort_keys=True,
            )
        )
        raise SystemExit(1) from exc
    return sitk


def version_string(sitk: Any) -> str:
    version_fn = getattr(sitk, "Version_VersionString", None)
    if callable(version_fn):
        return str(version_fn())
    version_obj = getattr(sitk, "Version", None)
    if callable(version_obj):
        return str(version_obj())
    return "unknown"


def image_check(sitk: Any) -> dict[str, Any]:
    image = sitk.Image([6, 5], sitk.sitkUInt8)
    image.SetSpacing([0.7, 1.4])
    image.SetOrigin([2.0, -3.0])
    image.SetPixel(2, 3, 17)
    point = image.TransformIndexToPhysicalPoint([2, 3])
    return {
        "size": list(image.GetSize()),
        "spacing": [float(value) for value in image.GetSpacing()],
        "origin": [float(value) for value in image.GetOrigin()],
        "pixel_id": image.GetPixelIDTypeAsString(),
        "sample_pixel": int(image.GetPixel(2, 3)),
        "sample_physical_point": [float(value) for value in point],
    }


def numpy_check(sitk: Any, skip_numpy: bool) -> dict[str, Any]:
    if skip_numpy:
        return {"skipped": True, "reason": "--skip-numpy"}
    try:
        import numpy as np  # type: ignore
    except Exception as exc:
        return {"available": False, "error": str(exc)}

    array = np.zeros((3, 4, 5), dtype=np.uint8)
    array[1, 2, 3] = 9
    image = sitk.GetImageFromArray(array)
    copied = sitk.GetArrayFromImage(image)
    view = sitk.GetArrayViewFromImage(image)
    return {
        "available": True,
        "array_shape_zyx": list(array.shape),
        "image_size_xyz": list(image.GetSize()),
        "round_trip_equal": bool(np.array_equal(array, copied)),
        "view_writeable": bool(view.flags.writeable),
    }


def image_io_check(sitk: Any) -> dict[str, Any]:
    reader_ios = list(sitk.ImageFileReader().GetRegisteredImageIOs())
    writer_ios = list(sitk.ImageFileWriter().GetRegisteredImageIOs())
    return {
        "reader_count": len(reader_ios),
        "writer_count": len(writer_ios),
        "reader_examples": reader_ios[:12],
        "writer_examples": writer_ios[:12],
        "has_gdcm_reader": "GDCMImageIO" in reader_ios,
        "has_metaimage_writer": "MetaImageIO" in writer_ios,
    }


def registration_check(sitk: Any) -> dict[str, Any]:
    fixed = sitk.GaussianSource(sitk.sitkFloat32, [32, 32], [5.0, 5.0], [16.0, 16.0])
    transform = sitk.TranslationTransform(2, [1.5, -2.0])
    moved = sitk.Resample(fixed, fixed, transform, sitk.sitkLinear, 0.0, fixed.GetPixelID())
    registration = sitk.ImageRegistrationMethod()
    return {
        "has_image_registration_method": hasattr(sitk, "ImageRegistrationMethod"),
        "translation_parameters": [float(value) for value in transform.GetParameters()],
        "resampled_size": list(moved.GetSize()),
        "metric_constants": {
            "random_sampling": hasattr(registration, "RANDOM"),
            "regular_sampling": hasattr(registration, "REGULAR"),
            "none_sampling": hasattr(registration, "NONE"),
        },
    }


def optional_check(sitk: Any) -> dict[str, Any]:
    return {
        "ElastixImageFilter": hasattr(sitk, "ElastixImageFilter"),
        "TransformixImageFilter": hasattr(sitk, "TransformixImageFilter"),
        "note": "Elastix/transformix wrappers are optional and build-dependent.",
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    sitk = import_simpleitk()
    result = {
        "ok": True,
        "simpleitk_version": version_string(sitk),
        "image": image_check(sitk),
        "numpy": numpy_check(sitk, args.skip_numpy),
        "image_io": image_io_check(sitk),
        "registration": registration_check(sitk),
        "optional_features": optional_check(sitk),
    }
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
