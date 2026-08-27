#!/usr/bin/env python3
"""Smoke-test SimpleITK image and transform IO with generated data."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any


def require_simpleitk():
    try:
        import SimpleITK as sitk
    except Exception as exc:  # pragma: no cover - depends on host install
        raise RuntimeError(
            "Unable to import SimpleITK. Install the 'simpleitk' distribution "
            "or run this helper in an environment where 'import SimpleITK as sitk' works."
        ) from exc
    return sitk


def image_digest(sitk: Any, image: Any) -> str:
    payload = {
        "hash": sitk.Hash(image),
        "size": list(image.GetSize()),
        "spacing": list(image.GetSpacing()),
        "origin": list(image.GetOrigin()),
        "direction": list(image.GetDirection()),
        "pixel_id": image.GetPixelID(),
        "components": image.GetNumberOfComponentsPerPixel(),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def create_test_image(sitk: Any) -> Any:
    image = sitk.Image([8, 6], sitk.sitkUInt16)
    image.SetSpacing((0.7, 1.25))
    image.SetOrigin((3.0, -2.0))
    image.SetDirection((0.0, -1.0, 1.0, 0.0))
    image.SetMetaData("simpleitk.smoke", "io-roundtrip")
    for y_index in range(image.GetHeight()):
        for x_index in range(image.GetWidth()):
            image[x_index, y_index] = x_index + 10 * y_index
    return image


def assert_image_roundtrip(sitk: Any, original: Any, read_back: Any) -> dict[str, bool]:
    checks = {
        "size_equal": original.GetSize() == read_back.GetSize(),
        "spacing_equal": original.GetSpacing() == read_back.GetSpacing(),
        "origin_equal": original.GetOrigin() == read_back.GetOrigin(),
        "direction_equal": original.GetDirection() == read_back.GetDirection(),
        "pixel_id_equal": original.GetPixelID() == read_back.GetPixelID(),
        "hash_equal": sitk.Hash(original) == sitk.Hash(read_back),
        "metadata_value_equal": read_back.HasMetaDataKey("simpleitk.smoke")
        and read_back.GetMetaData("simpleitk.smoke") == "io-roundtrip",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise AssertionError("image round-trip checks failed: " + ", ".join(failed))
    return checks


def assert_transform_roundtrip(sitk: Any, transform_path: Path) -> dict[str, bool]:
    transform = sitk.Euler2DTransform()
    transform.SetAngle(0.125)
    transform.SetCenter((1.0, 2.0))
    transform.SetTranslation((2.0, 3.0))

    sitk.WriteTransform(transform, str(transform_path))
    read_back = sitk.ReadTransform(str(transform_path))

    checks = {
        "type_equal": isinstance(read_back, sitk.Euler2DTransform),
        "dimension_equal": read_back.GetDimension() == transform.GetDimension(),
        "parameters_equal": tuple(read_back.GetParameters()) == tuple(transform.GetParameters()),
        "fixed_parameters_equal": tuple(read_back.GetFixedParameters())
        == tuple(transform.GetFixedParameters()),
        "point_mapping_equal": tuple(read_back.TransformPoint((4.0, 5.0)))
        == tuple(transform.TransformPoint((4.0, 5.0))),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise AssertionError("transform round-trip checks failed: " + ", ".join(failed))
    return checks


def registered_image_ios(sitk: Any) -> dict[str, list[str]]:
    reader_ios = list(sitk.ImageFileReader().GetRegisteredImageIOs())
    writer_ios = list(sitk.ImageFileWriter().GetRegisteredImageIOs())
    return {"reader": reader_ios, "writer": writer_ios}


def run_smoke(output_dir: Path, image_io: str, keep_outputs: bool) -> dict[str, Any]:
    sitk = require_simpleitk()
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / "simpleitk_io_smoke.mha"
    transform_path = output_dir / "simpleitk_euler2d_smoke.tfm"

    original = create_test_image(sitk)
    write_kwargs: dict[str, Any] = {"useCompression": True}
    if image_io:
        write_kwargs["imageIO"] = image_io
    sitk.WriteImage(original, str(image_path), **write_kwargs)

    read_kwargs: dict[str, Any] = {}
    if image_io:
        read_kwargs["imageIO"] = image_io
    read_back = sitk.ReadImage(str(image_path), **read_kwargs)

    image_checks = assert_image_roundtrip(sitk, original, read_back)
    transform_checks = assert_transform_roundtrip(sitk, transform_path)
    ios = registered_image_ios(sitk)

    result = {
        "ok": True,
        "simpleitk_version": getattr(sitk, "Version_VersionString", lambda: "unknown")(),
        "registered_image_ios": ios,
        "image_file": str(image_path) if keep_outputs else None,
        "image_io": image_io or "auto",
        "image_digest": image_digest(sitk, read_back),
        "image_checks": image_checks,
        "transform_file": str(transform_path) if keep_outputs else None,
        "transform_type": sitk.ReadTransform(str(transform_path)).GetName(),
        "transform_checks": transform_checks,
    }
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create generated SimpleITK data, round-trip image and transform IO, "
            "and print JSON results. By default outputs are created in a temporary "
            "directory and removed after the check."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for smoke-test files. If omitted, a temporary directory is used.",
    )
    parser.add_argument(
        "--keep-outputs",
        action="store_true",
        help="Keep generated files and include their paths in the JSON output. Requires or creates --output-dir.",
    )
    parser.add_argument(
        "--image-io",
        default="",
        help="Optional ImageIO backend to force, such as MetaImageIO. Defaults to auto-selection.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.output_dir is None and not args.keep_outputs:
            with tempfile.TemporaryDirectory(prefix="simpleitk-io-smoke-") as temporary_dir:
                result = run_smoke(Path(temporary_dir), args.image_io, keep_outputs=False)
        else:
            output_dir = args.output_dir or Path("simpleitk-io-smoke-output")
            result = run_smoke(output_dir, args.image_io, keep_outputs=True)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "hint": (
                        "Use --image-io MetaImageIO for the default .mha smoke format, "
                        "check registered ImageIOs via ImageFileReader/ImageFileWriter, "
                        "and confirm SimpleITK imports as 'import SimpleITK as sitk'."
                    ),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
