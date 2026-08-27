#!/usr/bin/env python3
"""Probe img2dataset resize, encode, filter, and bbox blur options.

The helper builds synthetic images in memory, encodes them using the same
format you ask the probe to produce, and then runs the img2dataset Resizer on
those streams. This makes it useful for checking resize gates, codec choices,
filter errors, skip-reencode behavior, and bbox blur wiring without touching
network resources or repository fixtures.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
from typing import Any

os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")


def _choices() -> list[str]:
    return ["no", "border", "keep_ratio", "keep_ratio_largest", "center_crop"]


def _interp_choices() -> list[str]:
    return ["nearest", "linear", "bilinear", "cubic", "bicubic", "area", "lanczos", "lanczos4"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe img2dataset image-processing options on synthetic images.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--mode", choices=_choices(), default="border", help="Resize mode to probe.")
    parser.add_argument("--image-size", type=int, default=256, help="Target image size passed to Resizer.")
    parser.add_argument(
        "--encode-format",
        choices=["jpg", "png", "webp"],
        default="jpg",
        help="Output encode format to probe.",
    )
    parser.add_argument("--encode-quality", type=int, default=95, help="Encode quality or PNG compression.")
    parser.add_argument(
        "--resize-only-if-bigger",
        action="store_true",
        help="Only apply the resize branch when the relevant side exceeds image-size.",
    )
    parser.add_argument("--min-image-size", type=int, default=0, help="Minimum accepted side length.")
    parser.add_argument(
        "--max-image-area",
        type=float,
        default=float("inf"),
        help="Maximum accepted pixel area.",
    )
    parser.add_argument(
        "--max-aspect-ratio",
        type=float,
        default=float("inf"),
        help="Maximum accepted aspect ratio.",
    )
    parser.add_argument(
        "--upscale-interpolation",
        choices=_interp_choices(),
        default="lanczos",
        help="Interpolation used when the helper upscales a sample.",
    )
    parser.add_argument(
        "--downscale-interpolation",
        choices=_interp_choices(),
        default="area",
        help="Interpolation used when the helper downscales a sample.",
    )
    parser.add_argument(
        "--skip-reencode",
        action="store_true",
        help="Ask Resizer to keep original bytes when the image does not change.",
    )
    parser.add_argument(
        "--disable-all-reencoding",
        action="store_true",
        help="Bypass decoding, validation, resizing, blur, and reencoding.",
    )
    parser.add_argument(
        "--with-bbox",
        action="store_true",
        help="Attach a fixed normalized bbox list and exercise BoundingBoxBlurrer.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, float) and math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return value


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: _json_safe(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(value) for value in obj]
    return _normalize_scalar(obj)


def _synthetic_cases(image_size: int) -> list[tuple[str, int, int]]:
    small = max(8, image_size // 4)
    big = max(image_size + 64, (image_size * 3) // 2)
    return [
        ("tiny_square", small, small),
        ("target_square", image_size, image_size),
        ("oversize_square", big, big),
        ("wide", big, small),
        ("tall", small, big),
    ]


def _make_synthetic_image(width: int, height: int):
    import cv2
    import numpy as np

    yy, xx = np.indices((height, width))
    image = np.empty((height, width, 3), dtype=np.uint8)
    image[:, :, 0] = (xx * 255 // max(1, width - 1)).astype(np.uint8)
    image[:, :, 1] = (yy * 255 // max(1, height - 1)).astype(np.uint8)
    image[:, :, 2] = ((xx + yy) * 255 // max(1, width + height - 2)).astype(np.uint8)

    x1, y1 = width // 4, height // 4
    x2, y2 = max(x1 + 1, (3 * width) // 4), max(y1 + 1, (3 * height) // 4)
    cv2.rectangle(image, (x1, y1), (x2 - 1, y2 - 1), (0, 255, 255), thickness=-1)
    return image


def _encode_image(image, encode_format: str, encode_quality: int) -> bytes:
    import cv2

    if encode_format == "jpg":
        params = [int(cv2.IMWRITE_JPEG_QUALITY), encode_quality]
        ext = ".jpg"
    elif encode_format == "png":
        params = [int(cv2.IMWRITE_PNG_COMPRESSION), encode_quality]
        ext = ".png"
    else:
        params = [int(cv2.IMWRITE_WEBP_QUALITY), encode_quality]
        ext = ".webp"

    ok, encoded = cv2.imencode(ext, image, params=params)
    if not ok:
        raise RuntimeError(f"OpenCV could not encode synthetic source as {encode_format}")
    return encoded.tobytes()


def _build_resizer(args):
    from img2dataset.blurrer import BoundingBoxBlurrer
    from img2dataset.resizer import Resizer

    blurrer = BoundingBoxBlurrer() if args.with_bbox else None
    return Resizer(
        image_size=args.image_size,
        resize_mode=args.mode,
        resize_only_if_bigger=args.resize_only_if_bigger,
        upscale_interpolation=args.upscale_interpolation,
        downscale_interpolation=args.downscale_interpolation,
        encode_quality=args.encode_quality,
        encode_format=args.encode_format,
        skip_reencode=args.skip_reencode,
        disable_all_reencoding=args.disable_all_reencoding,
        min_image_size=args.min_image_size,
        max_image_area=args.max_image_area,
        max_aspect_ratio=args.max_aspect_ratio,
        blurrer=blurrer,
    )


def _bbox_list() -> list[list[float]]:
    return [
        [0.20, 0.20, 0.50, 0.55],
        [0.58, 0.28, 0.88, 0.78],
    ]


def _run_case(resizer, name: str, width: int, height: int, args) -> dict[str, Any]:
    source_image = _make_synthetic_image(width, height)
    input_bytes = _encode_image(source_image, args.encode_format, args.encode_quality)
    stream = io.BytesIO(input_bytes)
    bbox_list = _bbox_list() if args.with_bbox else None

    try:
        output_bytes, out_w, out_h, orig_w, orig_h, err = resizer(stream, blurring_bbox_list=bbox_list)
    except Exception as exc:  # pragma: no cover - defensive probe behavior
        return {
            "name": name,
            "input_width": width,
            "input_height": height,
            "error": f"unexpected exception: {exc}",
        }

    same_bytes = output_bytes == input_bytes if output_bytes is not None else False
    result: dict[str, Any] = {
        "name": name,
        "input_width": width,
        "input_height": height,
        "output_width": out_w,
        "output_height": out_h,
        "original_width": orig_w,
        "original_height": orig_h,
        "error": err,
        "input_bytes": len(input_bytes),
        "output_bytes": len(output_bytes) if output_bytes is not None else None,
        "same_as_input": same_bytes,
    }
    if bbox_list is not None:
        result["bbox_list"] = bbox_list
    return result


def run_probe(args) -> list[dict[str, Any]]:
    if args.image_size < 1:
        raise ValueError("--image-size must be at least 1")
    if args.encode_format == "png" and not 0 <= args.encode_quality <= 9:
        raise ValueError("For png, encode quality represents compression and must be between 0 and 9")

    resizer = _build_resizer(args)
    results = []
    for name, width, height in _synthetic_cases(args.image_size):
        results.append(_run_case(resizer, name, width, height, args))
    return results


def _print_text(args, results: list[dict[str, Any]]) -> None:
    print(
        f"mode={args.mode} image_size={args.image_size} encode_format={args.encode_format} "
        f"encode_quality={args.encode_quality} resize_only_if_bigger={args.resize_only_if_bigger} "
        f"skip_reencode={args.skip_reencode} disable_all_reencoding={args.disable_all_reencoding} "
        f"with_bbox={args.with_bbox}"
    )
    for row in results:
        if row.get("error") and row.get("output_width") is None and row.get("output_height") is None:
            print(
                f"- {row['name']}: input={row['input_width']}x{row['input_height']} "
                f"err={row['error']}"
            )
            continue
        if args.disable_all_reencoding:
            print(
                f"- {row['name']}: input={row['input_width']}x{row['input_height']} "
                f"raw_passthrough output=n/a original=n/a "
                f"bytes_in={row['input_bytes']} bytes_out={row['output_bytes']} "
                f"same_as_input={row['same_as_input']}"
            )
        else:
            print(
                f"- {row['name']}: input={row['input_width']}x{row['input_height']} -> "
                f"output={row['output_width']}x{row['output_height']} "
                f"original={row['original_width']}x{row['original_height']} "
                f"err={row['error']} bytes_in={row['input_bytes']} bytes_out={row['output_bytes']} "
                f"same_as_input={row['same_as_input']}"
            )
        if row.get("bbox_list") is not None:
            print(f"  bbox_list={row['bbox_list']}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        results = run_probe(args)
    except Exception as exc:
        payload = {"error": str(exc)}
        if args.json:
            print(json.dumps(_json_safe(payload), indent=2))
        else:
            print(f"config error: {exc}")
        return 2

    payload = {
        "mode": args.mode,
        "image_size": args.image_size,
        "encode_format": args.encode_format,
        "encode_quality": args.encode_quality,
        "resize_only_if_bigger": args.resize_only_if_bigger,
        "skip_reencode": args.skip_reencode,
        "disable_all_reencoding": args.disable_all_reencoding,
        "with_bbox": args.with_bbox,
        "filters": {
            "min_image_size": args.min_image_size,
            "max_image_area": args.max_image_area,
            "max_aspect_ratio": args.max_aspect_ratio,
        },
        "interpolation": {
            "upscale": args.upscale_interpolation,
            "downscale": args.downscale_interpolation,
        },
        "samples": results,
    }

    if args.json:
        print(json.dumps(_json_safe(payload), indent=2))
    else:
        _print_text(args, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
