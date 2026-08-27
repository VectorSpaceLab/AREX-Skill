#!/usr/bin/env python3
"""Validate aligned guided-editing image, mask, and trimap contracts.

This is a read-only preflight. It deliberately does not run a model, call a
network, invoke GIMP, or write an output file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from PIL import Image, UnidentifiedImageError


FACE_PALETTE = {
    (0, 0, 0),
    (204, 0, 0),
    (76, 153, 0),
    (204, 204, 0),
    (51, 51, 255),
    (204, 0, 204),
    (0, 255, 255),
    (51, 255, 255),
    (102, 51, 0),
    (255, 0, 0),
    (102, 204, 0),
    (255, 255, 0),
    (0, 0, 153),
    (0, 0, 204),
    (255, 51, 153),
    (0, 204, 204),
    (0, 51, 0),
    (255, 153, 51),
    (0, 204, 0),
}


class Validation:
    """Collect errors and warnings so the report remains useful on bad input."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Read-only validation for GIMP-ML guided-editing inputs. "
            "Choose exactly one route: --mask, --trimap, face masks, or "
            "--color-mask. No model or network is used."
        ),
        epilog=(
            "Examples: --image photo.png --mask remove.png; "
            "--image photo.png --trimap trimap.png; "
            "--portrait face.png --original-mask original.png "
            "--modified-mask changed.png; --image gray-rgb.png "
            "--color-mask points.png"
        ),
    )
    p.add_argument("--image", type=Path, help="base RGB/RGBA image")
    p.add_argument("--mask", type=Path, help="inpainting mask (L, LA, RGB, or RGBA)")
    p.add_argument("--trimap", type=Path, help="matting trimap (RGB or RGBA)")
    p.add_argument("--portrait", type=Path, help="portrait for the face route")
    p.add_argument("--original-mask", type=Path, help="original face label mask")
    p.add_argument("--modified-mask", type=Path, help="modified face label mask")
    p.add_argument("--color-mask", type=Path, help="optional transparent RGBA color mask")
    p.add_argument(
        "--trimap-tolerance",
        type=float,
        default=0.0,
        metavar="N",
        help="accept trimap channel values within N of 0, 128, or 255 (default: 0)",
    )
    return p


def load_image(path: Path | None, label: str, result: Validation):
    """Load without converting, retaining channel/mode information."""
    if path is None:
        result.error(f"{label}: an explicit image path is required")
        return None
    try:
        with Image.open(path) as source:
            image = source.copy()
            mode = source.mode
    except (FileNotFoundError, PermissionError) as exc:
        result.error(f"{label}: cannot read {path}: {exc}")
        return None
    except (UnidentifiedImageError, OSError) as exc:
        result.error(f"{label}: not a readable image file {path}: {exc}")
        return None

    array = np.asarray(image)
    if array.ndim == 2:
        channels = 1
    elif array.ndim == 3:
        channels = array.shape[2]
    else:
        channels = 0
    if channels not in (1, 2, 3, 4):
        result.error(f"{label}: unsupported channel shape {array.shape} (mode {mode})")
        return None
    if array.dtype.kind not in "uib":
        result.error(f"{label}: unsupported pixel dtype {array.dtype}; use an 8-bit image")
        return None
    if array.dtype.itemsize != 1:
        result.error(f"{label}: {mode} is not an 8-bit image; export 8-bit pixels")
        return None
    return {"path": path, "label": label, "array": array, "mode": mode, "channels": channels}


def shape_of(item) -> tuple[int, int]:
    array = item["array"]
    return int(array.shape[0]), int(array.shape[1])


def describe(item) -> str:
    h, w = shape_of(item)
    alpha = "yes" if item["channels"] in (2, 4) else "no"
    return f"{item['label']}: {w}x{h}, mode={item['mode']}, channels={item['channels']}, alpha={alpha}"


def first_channels(item) -> np.ndarray:
    array = item["array"]
    return array if array.ndim == 2 else array[:, :, :3]


def check_common_image(item, result: Validation, label: str) -> None:
    if item is None:
        return
    if item["channels"] not in (3, 4):
        result.error(f"{label}: requires RGB or RGBA, got {describe(item)}")


def check_alignment(items: Sequence, result: Validation) -> None:
    present = [item for item in items if item is not None]
    if len(present) < 2:
        return
    reference_shape = shape_of(present[0])
    for item in present[1:]:
        if shape_of(item) != reference_shape:
            result.error(
                f"shape mismatch: {present[0]['label']} is {reference_shape[1]}x{reference_shape[0]}, "
                f"but {item['label']} is {shape_of(item)[1]}x{shape_of(item)[0]}; "
                "layers/files must share the image canvas"
            )


def check_consistent_rgb(item, result: Validation, label: str) -> None:
    """Require RGB mask-like channels to encode one scalar value per pixel."""
    if item is None or item["channels"] not in (3, 4):
        return
    rgb = item["array"][:, :, :3]
    if not (np.array_equal(rgb[:, :, 0], rgb[:, :, 1]) and np.array_equal(rgb[:, :, 0], rgb[:, :, 2])):
        result.error(f"{label}: RGB channels disagree; expected one consistent mask/trimap value per pixel")


def check_inpainting(image, mask, result: Validation) -> None:
    if image is None or mask is None:
        return
    check_common_image(image, result, "image")
    if mask["channels"] not in (1, 2, 3, 4):
        result.error(f"mask: requires L, LA, RGB, or RGBA, got {describe(mask)}")
    check_consistent_rgb(mask, result, "mask")
    check_alignment([image, mask], result)
    values = first_channels(mask)
    values = values[:, :, 0] if values.ndim == 3 else values
    zeros = int(np.count_nonzero(values == 0))
    whites = int(np.count_nonzero(values == 255))
    intermediate = int(values.size - zeros - whites)
    print(f"inpainting polarity: 255 keep/background={whites}; 0 remove/object={zeros}; intermediate={intermediate}")
    print("  manual/user rule: 255 background and 0 object-to-remove (manual wording is visually counterintuitive)")
    print("  checked source path: normalizes as 1 - value/255, so it keeps 255 and removes 0; verify on the target host")
    if intermediate:
        result.error("mask: contains non-binary values; use exact 0 and 255 before inpainting")
    if zeros == 0 or whites == 0:
        result.warning("mask: only one binary polarity is present; review whether the whole image would be kept or removed")


def check_trimap(image, trimap, tolerance: float, result: Validation) -> None:
    if image is None or trimap is None:
        return
    check_common_image(image, result, "image")
    if trimap["channels"] not in (3, 4):
        result.error(f"trimap: requires RGB or RGBA so black/white/gray triplets are explicit, got {describe(trimap)}")
    check_consistent_rgb(trimap, result, "trimap")
    check_alignment([image, trimap], result)
    values = first_channels(trimap)
    values = values[:, :, 0] if values.ndim == 3 else values
    allowed = np.array([0.0, 128.0, 255.0])
    distances = np.min(np.abs(values.astype(np.float64)[..., None] - allowed), axis=2)
    outside = distances > tolerance
    exact = (values == 0) | (values == 128) | (values == 255)
    near = (~exact) & (~outside)
    if np.any(outside):
        bad = np.unique(values[outside])
        shown = ", ".join(str(int(v)) for v in bad[:12])
        suffix = "..." if bad.size > 12 else ""
        result.error(f"trimap: values outside 0/128/255 tolerance {tolerance:g}: {shown}{suffix}")
    if np.any(near):
        result.warning("trimap: near-allowed values accepted by tolerance; rewrite them as exact 0, 128, or 255 before model execution")
    boundary = int(np.count_nonzero(values == 128))
    background = int(np.count_nonzero(values == 0))
    foreground = int(np.count_nonzero(values == 255))
    print(f"trimap values: 0 background={background}; 128 gray boundary={boundary}; 255 object={foreground}")
    if boundary == 0:
        result.warning("trimap: no exact 128 gray boundary is present; matting has no explicit unknown region")


def check_face(portrait, original, modified, result: Validation) -> None:
    if portrait is None or original is None or modified is None:
        return
    check_common_image(portrait, result, "portrait")
    for label, item in (("original mask", original), ("modified mask", modified)):
        if item["channels"] not in (3, 4):
            result.error(f"{label}: requires RGB or RGBA face-label colors, got {describe(item)}")
        if item["channels"] in (3, 4):
            rgb = item["array"][:, :, :3]
            flattened = {tuple(pixel) for pixel in rgb.reshape(-1, 3)}
            invalid = flattened - FACE_PALETTE
            if invalid:
                examples = ", ".join(str(v) for v in sorted(invalid)[:4])
                result.error(f"{label}: contains unsupported/non-exact face palette colors, e.g. {examples}")
    check_alignment([portrait, original, modified], result)
    print("face route: portrait + original mask + modified mask are required; face parsing precedes generation")


def check_color(image, color_mask, result: Validation) -> None:
    if image is None or color_mask is None:
        return
    check_common_image(image, result, "image")
    if color_mask["channels"] != 4:
        result.error(f"color mask: requires RGBA with an alpha channel, got {describe(color_mask)}")
    check_alignment([image, color_mask], result)
    if color_mask["channels"] == 4:
        alpha = color_mask["array"][:, :, 3]
        visible = int(np.count_nonzero(alpha))
        print(f"color guidance: RGBA alpha-visible pixels={visible}/{alpha.size}; local RGB points are optional")
        if visible == 0:
            result.warning("color mask: fully transparent; it supplies no visible local color points")
    if image["channels"] == 3:
        rgb = image["array"][:, :, :3]
    elif image["channels"] == 4:
        rgb = image["array"][:, :, :3]
    else:
        rgb = None
    if rgb is not None and np.array_equal(rgb[:, :, 0], rgb[:, :, 1]) and np.array_equal(rgb[:, :, 1], rgb[:, :, 2]):
        print("image note: pixels are grayscale-looking but stored with RGB channels, as required by the manual")


def print_inputs(items: Iterable) -> None:
    for item in items:
        if item is not None:
            print(describe(item))


def choose_route(args, result: Validation) -> str | None:
    route_flags = [args.mask is not None, args.trimap is not None, args.color_mask is not None,
                   any(v is not None for v in (args.portrait, args.original_mask, args.modified_mask))]
    if sum(route_flags) != 1:
        result.error("choose exactly one route: --mask, --trimap, --color-mask, or all three face arguments")
        return None
    if args.mask is not None or args.trimap is not None or args.color_mask is not None:
        if args.image is None:
            result.error("--image is required for --mask, --trimap, and --color-mask routes")
        if args.portrait is not None or args.original_mask is not None or args.modified_mask is not None:
            result.error("face arguments cannot be combined with an image mask/trimap/color route")
        return "inpainting" if args.mask is not None else "matting" if args.trimap is not None else "coloring"
    if args.image is not None:
        result.error("use --portrait, not --image, for the face route")
    if any(v is None for v in (args.portrait, args.original_mask, args.modified_mask)):
        result.error("face route requires --portrait, --original-mask, and --modified-mask together")
    return "face" if not result.errors else None


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    result = Validation()
    route = choose_route(args, result)
    items = []

    if route == "inpainting":
        image = load_image(args.image, "image", result)
        mask = load_image(args.mask, "mask", result)
        items = [image, mask]
        print_inputs(items)
        check_inpainting(image, mask, result)
    elif route == "matting":
        image = load_image(args.image, "image", result)
        trimap = load_image(args.trimap, "trimap", result)
        items = [image, trimap]
        print_inputs(items)
        if not np.isfinite(args.trimap_tolerance) or args.trimap_tolerance < 0:
            result.error("--trimap-tolerance must be a finite non-negative number")
            tolerance = 0.0
        else:
            tolerance = args.trimap_tolerance
        check_trimap(image, trimap, tolerance, result)
    elif route == "coloring":
        image = load_image(args.image, "image", result)
        color_mask = load_image(args.color_mask, "color mask", result)
        items = [image, color_mask]
        print_inputs(items)
        check_color(image, color_mask, result)
    elif route == "face":
        portrait = load_image(args.portrait, "portrait", result)
        original = load_image(args.original_mask, "original mask", result)
        modified = load_image(args.modified_mask, "modified mask", result)
        items = [portrait, original, modified]
        print_inputs(items)
        check_face(portrait, original, modified, result)

    if result.warnings:
        print("WARNINGS:")
        for message in result.warnings:
            print(f"- {message}")
    if result.errors:
        print("ERRORS:", file=sys.stderr)
        for message in result.errors:
            print(f"- {message}", file=sys.stderr)
        print("validation: FAIL", file=sys.stderr)
        return 2
    if route is None:
        print("validation: FAIL", file=sys.stderr)
        return 2
    print(f"validation: PASS ({route} static contract only)")
    print("no model, network, GIMP mutation, credential, or weight operation was performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
