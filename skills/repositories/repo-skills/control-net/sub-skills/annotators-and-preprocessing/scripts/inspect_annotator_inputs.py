#!/usr/bin/env python3
"""Inspect ControlNet-style annotator preprocessing without loading detectors.

This helper intentionally avoids importing ControlNet annotator modules, Gradio,
Torch detector wrappers, checkpoint files, or network download utilities. It
implements the small HWC3/resize semantics needed to debug input images and can
optionally parse gradio_annotator.py with AST to list UI function signatures.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

PixelArray = list[Any]


def shape_of(array: PixelArray) -> list[int]:
    if not isinstance(array, list):
        raise ValueError("expected a list-backed image array")
    height = len(array)
    if height == 0:
        return [0]
    if not isinstance(array[0], list):
        return [height]
    width = len(array[0])
    if width == 0:
        return [height, width]
    first_pixel = array[0][0]
    if isinstance(first_pixel, list):
        return [height, width, len(first_pixel)]
    return [height, width]


def iter_values(array: PixelArray):
    shape = shape_of(array)
    if len(shape) == 2:
        for row in array:
            for value in row:
                yield value
    elif len(shape) == 3:
        for row in array:
            for pixel in row:
                for value in pixel:
                    yield value
    else:
        raise ValueError(f"expected 2D or 3D input, got shape {shape}")


def ensure_uint8(array: PixelArray) -> None:
    for value in iter_values(array):
        if not isinstance(value, int) or value < 0 or value > 255:
            raise ValueError("expected uint8-like integer values in [0, 255]")


def hwc3(array: PixelArray) -> PixelArray:
    """Return ControlNet-style uint8 HWC 3-channel image data."""
    ensure_uint8(array)
    shape = shape_of(array)
    if len(shape) == 2:
        return [[[value, value, value] for value in row] for row in array]
    if len(shape) != 3:
        raise ValueError(f"expected 2D or 3D input, got shape {shape}")

    channels = shape[2]
    if channels not in (1, 3, 4):
        raise ValueError(f"expected 1, 3, or 4 channels, got {channels}")
    if channels == 3:
        return [[list(pixel) for pixel in row] for row in array]
    if channels == 1:
        return [[[pixel[0], pixel[0], pixel[0]] for pixel in row] for row in array]

    composited: PixelArray = []
    for row in array:
        output_row = []
        for pixel in row:
            alpha = pixel[3] / 255.0
            output_row.append([int(min(255.0, max(0.0, channel * alpha + 255.0 * (1.0 - alpha)))) for channel in pixel[:3]])
        composited.append(output_row)
    return composited


def rounded_size(height: int, width: int, resolution: int) -> tuple[int, int, float]:
    """Return height, width after ControlNet short-side scaling and /64 rounding."""
    scale = float(resolution) / float(min(height, width))
    out_height = int(round((height * scale) / 64.0)) * 64
    out_width = int(round((width * scale) / 64.0)) * 64
    return out_height, out_width, scale


def summarize_array(label: str, array: PixelArray, resolution: int) -> dict[str, Any]:
    converted = hwc3(array)
    converted_shape = shape_of(converted)
    out_height, out_width, scale = rounded_size(converted_shape[0], converted_shape[1], resolution)
    values = list(iter_values(converted))
    return {
        "label": label,
        "input_shape": shape_of(array),
        "input_dtype": "uint8-like",
        "hwc3_shape": converted_shape,
        "resized_shape": [out_height, out_width, converted_shape[2]],
        "expected_resized_hw": [out_height, out_width],
        "scale_short_side": scale,
        "min_pixel_after_hwc3": min(values),
        "max_pixel_after_hwc3": max(values),
    }


def tiny_arrays() -> list[tuple[str, PixelArray]]:
    gray = [[0, 255], [64, 128]]
    one_channel = [[[value] for value in row] for row in gray]
    rgb = [[[value, 10, 200] for value in row] for row in gray]
    alphas = [[0, 128], [255, 64]]
    rgba = [[rgb[row_index][col_index] + [alphas[row_index][col_index]] for col_index in range(2)] for row_index in range(2)]
    return [
        ("gray_2d", gray),
        ("gray_1ch", one_channel),
        ("rgb_3ch", rgb),
        ("rgba_4ch", rgba),
    ]


def load_image(path: Path) -> PixelArray:
    try:
        from PIL import Image
    except Exception as exc:
        raise SystemExit(f"Pillow is required to inspect image files: {exc}") from exc
    with Image.open(path) as image:
        if image.mode in {"RGBA", "LA"}:
            converted = image.convert("RGBA")
            width, height = converted.size
            pixels = [list(pixel) for pixel in converted.getdata()]
            return [pixels[row * width : (row + 1) * width] for row in range(height)]
        if image.mode in {"L", "I;16", "I", "F"}:
            converted = image.convert("L")
            width, height = converted.size
            pixels = list(converted.getdata())
            return [pixels[row * width : (row + 1) * width] for row in range(height)]
        converted = image.convert("RGB")
        width, height = converted.size
        pixels = [list(pixel) for pixel in converted.getdata()]
        return [pixels[row * width : (row + 1) * width] for row in range(height)]


def parse_gradio_signatures(repo_root: Path) -> list[dict[str, Any]]:
    annotator_path = repo_root / "gradio_annotator.py"
    if not annotator_path.exists():
        raise FileNotFoundError(f"missing gradio_annotator.py under {repo_root}")
    tree = ast.parse(annotator_path.read_text(encoding="utf-8"), filename=str(annotator_path))
    interesting = {"canny", "hed", "mlsd", "midas", "openpose", "uniformer"}
    signatures: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in interesting:
            args = [arg.arg for arg in node.args.args]
            defaults = [ast.unparse(default) if hasattr(ast, "unparse") else "<default>" for default in node.args.defaults]
            signatures.append({"name": node.name, "args": args, "defaults": defaults, "line": node.lineno})
    return sorted(signatures, key=lambda item: item["name"])


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    if args.image:
        reports.append(summarize_array(str(args.image), load_image(args.image), args.resolution))
    if args.self_check or not args.image:
        for label, array in tiny_arrays():
            reports.append(summarize_array(label, array, args.resolution))

    output: dict[str, Any] = {
        "resolution": args.resolution,
        "preprocessing": "HWC3 uint8 conversion plus short-side resize rounded to multiples of 64",
        "images": reports,
    }
    if args.repo_root:
        output["gradio_annotator_signatures"] = parse_gradio_signatures(args.repo_root)
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate ControlNet-style HWC3 conversion and 64-multiple resizing without loading detector models."
    )
    parser.add_argument("--image", type=Path, help="Optional local image to inspect; supports grayscale/RGB/RGBA through Pillow.")
    parser.add_argument("--resolution", type=int, default=512, help="Target short-side resolution before 64-multiple rounding.")
    parser.add_argument("--repo-root", type=Path, help="Optional ControlNet checkout to statically parse gradio_annotator.py signatures.")
    parser.add_argument("--self-check", action="store_true", help="Also run generated tiny grayscale/RGB/RGBA fixtures.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    if args.resolution <= 0:
        parser.error("--resolution must be positive")
    if args.image and not args.image.exists():
        parser.error(f"--image does not exist: {args.image}")
    if args.repo_root and not args.repo_root.exists():
        parser.error(f"--repo-root does not exist: {args.repo_root}")

    report = build_report(args)
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
