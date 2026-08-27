#!/usr/bin/env python3
"""Validate InternGPT-style image and mask inputs safely.

This script performs only local file checks:
- existence
- allowed extension
- PIL readability
- positive dimensions
- non-empty mask content
- optional parent-image relationship based on the generated filename anchor

It does not import any InternGPT modules or model dependencies.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Optional, Tuple

from PIL import Image

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


class ValidationError(Exception):
    """Raised when a mask or image input fails a safe precheck."""


def ensure_file(path: Path, label: str) -> None:
    if not path.exists():
        raise ValidationError(f"{label} does not exist: {path}")
    if not path.is_file():
        raise ValidationError(f"{label} is not a file: {path}")


def ensure_extension(path: Path, label: str, allowed: Iterable[str] = ALLOWED_EXTENSIONS) -> None:
    suffix = path.suffix.lower()
    if suffix not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValidationError(f"{label} has unsupported extension {suffix!r}; allowed: {allowed_text}")


def read_image(path: Path, label: str) -> Tuple[int, int]:
    try:
        with Image.open(path) as img:
            img.verify()
        with Image.open(path) as img:
            width, height = img.size
    except Exception as exc:  # pragma: no cover - exercised in real use, not unit-only syntax checks
        raise ValidationError(f"{label} is not a readable image: {path} ({exc})") from exc

    if width <= 0 or height <= 0:
        raise ValidationError(f"{label} has invalid dimensions: {width}x{height}")
    return width, height


def mask_non_empty(path: Path) -> bool:
    with Image.open(path) as img:
        mask = img.convert("L")
        return mask.getbbox() is not None


def mask_anchor(path: Path) -> Optional[str]:
    parts = path.stem.split("_")
    if len(parts) < 2:
        return None
    anchor = parts[1].strip()
    return anchor or None


def parent_prefix(path: Path) -> str:
    return path.stem.split("_")[0]


def validate_parent_relationship(image_path: Path, mask_path: Path) -> str:
    anchor = mask_anchor(mask_path)
    if anchor is None:
        raise ValidationError(
            f"Cannot infer a parent anchor from mask filename: {mask_path.name}"
        )

    if parent_prefix(image_path) != anchor:
        raise ValidationError(
            "Image and mask do not share the expected generated parent anchor: "
            f"image={image_path.name!r}, mask={mask_path.name!r}, expected anchor={anchor!r}"
        )

    return anchor


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Path to the source image.")
    parser.add_argument("--mask", required=True, help="Path to the mask image.")
    parser.add_argument(
        "--parent",
        help="Optional explicit parent image path to confirm the mask anchor.",
    )
    parser.add_argument(
        "--check-parent",
        action="store_true",
        help="Require the mask filename anchor to match the --image path prefix.",
    )
    parser.add_argument(
        "--allow-size-mismatch",
        action="store_true",
        help="Allow the image and mask to have different dimensions.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    image_path = Path(args.image).expanduser()
    mask_path = Path(args.mask).expanduser()
    parent_path = Path(args.parent).expanduser() if args.parent else None

    try:
        ensure_file(image_path, "image")
        ensure_file(mask_path, "mask")
        ensure_extension(image_path, "image")
        ensure_extension(mask_path, "mask")
        image_size = read_image(image_path, "image")
        mask_size = read_image(mask_path, "mask")

        if not args.allow_size_mismatch and image_size != mask_size:
            raise ValidationError(
                f"image and mask dimensions differ: image={image_size[0]}x{image_size[1]}, "
                f"mask={mask_size[0]}x{mask_size[1]}"
            )

        if not mask_non_empty(mask_path):
            raise ValidationError(f"mask is empty: {mask_path}")

        anchor = mask_anchor(mask_path)
        if args.check_parent:
            anchor = validate_parent_relationship(image_path, mask_path)

        if parent_path is not None:
            ensure_file(parent_path, "parent")
            ensure_extension(parent_path, "parent")
            read_image(parent_path, "parent")
            if anchor is None:
                raise ValidationError(
                    f"Cannot infer a parent anchor from mask filename: {mask_path.name}"
                )
            if parent_prefix(parent_path) != anchor:
                raise ValidationError(
                    f"parent path does not match the inferred mask anchor: parent={parent_path.name!r}, "
                    f"anchor={anchor!r}"
                )

        print(f"OK image={image_path} size={image_size[0]}x{image_size[1]}")
        print(f"OK mask={mask_path} size={mask_size[0]}x{mask_size[1]} nonempty=True")
        print(f"OK parent-anchor={anchor or 'not-inferred'}")
        if args.check_parent:
            print("OK image-mask-parent-check=True")
        if parent_path is not None:
            print(f"OK parent={parent_path}")
        return 0
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
