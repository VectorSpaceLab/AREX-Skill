#!/usr/bin/env python3
"""Read-only validation for a small image array.

This is a bundled, adapted helper for the classical-image-ops skill; it is not
an original repository script. It reads one explicit .npy or image file, checks
an image-like shape, channels, dtype, numeric range, and optional dimensions,
and prints a compact report. It never writes a converted file, calls GIMP,
uses a network, or loads model weights.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

import numpy as np


class ValidationError(ValueError):
    """An input failed an intentional validation rule."""


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    return parsed


def load_array(path: Path) -> Tuple[np.ndarray, str]:
    """Load one explicit input without permitting object-pickle execution."""
    if not path.is_file():
        raise ValidationError(f"input does not exist or is not a regular file: {path}")

    if path.suffix.lower() == ".npy":
        try:
            # mmap avoids an unnecessary full copy for ordinary .npy inputs.
            return np.load(path, mmap_mode="r", allow_pickle=False), "npy"
        except (ValueError, OSError) as exc:
            raise ValidationError(f"could not read safe NumPy .npy input: {exc}") from exc

    try:
        from PIL import Image
    except ImportError as exc:
        raise ValidationError(
            "Pillow is required for image files; use an .npy input or install Pillow"
        ) from exc

    try:
        with Image.open(path) as image:
            # np.asarray reads pixels while the context keeps the decoder alive.
            return np.asarray(image), f"image/{image.format or 'unknown'}"
    except (OSError, ValueError) as exc:
        raise ValidationError(f"could not decode image input: {exc}") from exc


def image_channels(array: np.ndarray) -> int:
    if array.ndim == 2:
        return 1
    if array.ndim == 3:
        return int(array.shape[2])
    raise ValidationError(
        f"unsupported rank {array.ndim}; expected a non-empty (H, W) or (H, W, C) array"
    )


def scan_range(array: np.ndarray, lower: float, upper: float) -> Tuple[float, float]:
    """Check finiteness and bounds in chunks to avoid a full boolean copy."""
    flat = array.reshape(-1)
    observed_min: Optional[float] = None
    observed_max: Optional[float] = None
    chunk_size = 1_000_000
    is_float = np.issubdtype(array.dtype, np.floating)

    for start in range(0, flat.size, chunk_size):
        chunk = flat[start : start + chunk_size]
        if is_float and not np.isfinite(chunk).all():
            raise ValidationError("array contains NaN or infinite values")
        chunk_min = chunk.min()
        chunk_max = chunk.max()
        if observed_min is None or chunk_min < observed_min:
            observed_min = float(chunk_min)
        if observed_max is None or chunk_max > observed_max:
            observed_max = float(chunk_max)

    # The non-empty check occurs before this function, so these are defensive.
    if observed_min is None or observed_max is None:
        raise ValidationError("array has no values to scan")
    if observed_min < lower or observed_max > upper:
        raise ValidationError(
            f"value range [{observed_min:g}, {observed_max:g}] is outside "
            f"the inclusive allowed range [{lower:g}, {upper:g}]"
        )
    return observed_min, observed_max


def validate(
    array: np.ndarray,
    *,
    source_kind: str,
    expected_channels: Optional[int],
    expected_size: Optional[Tuple[int, int]],
    required_dtype: Optional[np.dtype],
    lower: float,
    upper: float,
    max_elements: Optional[int],
) -> Tuple[int, float, float]:
    if not isinstance(array, np.ndarray):
        array = np.asarray(array)
    if array.ndim not in (2, 3) or any(d <= 0 for d in array.shape):
        raise ValidationError(
            f"unsupported or empty shape {tuple(array.shape)}; expected positive rank-2 or rank-3 data"
        )
    if np.issubdtype(array.dtype, np.bool_) or not np.issubdtype(array.dtype, np.number):
        raise ValidationError(f"unsupported dtype {array.dtype}; expected numeric non-boolean data")
    if np.issubdtype(array.dtype, np.complexfloating):
        raise ValidationError(f"unsupported complex dtype {array.dtype}; expected real image data")
    if max_elements is not None and array.size > max_elements:
        raise ValidationError(
            f"array has {array.size} elements, above the requested --max-elements {max_elements}"
        )
    if not np.isfinite(lower) or not np.isfinite(upper) or lower > upper:
        raise ValidationError("range bounds must be finite and min <= max")

    channels = image_channels(array)
    if channels not in (1, 3, 4):
        raise ValidationError(
            f"unsupported channel count {channels}; expected 1, 3, or 4 channels"
        )
    if expected_channels is not None and channels != expected_channels:
        raise ValidationError(
            f"expected {expected_channels} channels but input has {channels}"
        )
    if expected_size is not None and tuple(array.shape[:2]) != expected_size:
        raise ValidationError(
            f"expected spatial size {expected_size[0]}x{expected_size[1]} but input is "
            f"{array.shape[0]}x{array.shape[1]}"
        )
    if required_dtype is not None and array.dtype != required_dtype:
        raise ValidationError(f"expected dtype {required_dtype} but input has {array.dtype}")

    observed_min, observed_max = scan_range(array, lower, upper)
    return channels, observed_min, observed_max


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate one explicit .npy or image file without writing output.",
        epilog=(
            "Examples: validate_image_array.py frame.npy --channels 3 "
            "--expected-size 256 256; "
            "validate_image_array.py frame.png --require-dtype uint8"
        ),
    )
    parser.add_argument("input", type=Path, help="explicit .npy or readable image file")
    parser.add_argument(
        "--channels",
        type=int,
        choices=(1, 3, 4),
        help="require this exact channel count; default still rejects unsupported counts",
    )
    parser.add_argument(
        "--expected-size",
        nargs=2,
        type=positive_int,
        metavar=("HEIGHT", "WIDTH"),
        help="require exact spatial dimensions",
    )
    parser.add_argument(
        "--require-dtype",
        metavar="DTYPE",
        help="require a NumPy dtype name, such as uint8 or float32",
    )
    parser.add_argument(
        "--min-value",
        type=float,
        default=0.0,
        help="inclusive lower value bound (default: 0)",
    )
    parser.add_argument(
        "--max-value",
        type=float,
        default=255.0,
        help="inclusive upper value bound (default: 255)",
    )
    parser.add_argument(
        "--max-elements",
        type=positive_int,
        help="optional element-count guard before scanning values",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        required_dtype = np.dtype(args.require_dtype) if args.require_dtype else None
        array, source_kind = load_array(args.input)
        channels, observed_min, observed_max = validate(
            array,
            source_kind=source_kind,
            expected_channels=args.channels,
            expected_size=tuple(args.expected_size) if args.expected_size else None,
            required_dtype=required_dtype,
            lower=args.min_value,
            upper=args.max_value,
            max_elements=args.max_elements,
        )
    except TypeError as exc:
        print(f"ERROR: invalid dtype or argument value: {exc}", file=sys.stderr)
        return 2
    except (ValidationError, MemoryError) as exc:
        label = "memory error" if isinstance(exc, MemoryError) else "validation error"
        print(f"ERROR ({label}): {exc}", file=sys.stderr)
        return 2

    print(f"OK: source={args.input} format={source_kind}")
    print(
        f"shape={tuple(array.shape)} channels={channels} dtype={array.dtype} "
        f"range=[{observed_min:g}, {observed_max:g}]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
