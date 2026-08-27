#!/usr/bin/env python3
"""Inspect a MedMNIST-shaped NPZ without importing PyTorch.

This is a conservative adaptation of the project's no-PyTorch loading idea.
It reads a caller-provided local NPZ or creates a tiny, temporary grayscale
fixture. It never downloads data and never overwrites a caller file.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile
import zipfile
from typing import Optional

import numpy as np


REQUIRED_KEYS = {
    "train_images",
    "train_labels",
    "val_images",
    "val_labels",
    "test_images",
    "test_labels",
}
SPLITS = ("train", "val", "test")
SIZES_2D = (28, 64, 128, 224)
SIZES_3D = (28, 64)


class ValidationError(ValueError):
    """An actionable local input or schema error."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and sample a MedMNIST-shaped NPZ without PyTorch or network access."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--npz",
        type=Path,
        help="existing local .npz file; it is opened read-only and never modified",
    )
    source.add_argument(
        "--fixture",
        choices=("2d", "3d"),
        help="create a temporary two-sample grayscale fixture instead of reading a file",
    )
    parser.add_argument(
        "--kind",
        choices=("auto", "2d", "3d"),
        default="auto",
        help="interpret the image arrays as 2D or 3D (default: infer from shape)",
    )
    parser.add_argument(
        "--split",
        choices=SPLITS,
        default="train",
        help="split to inspect (default: train)",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="sample index to convert (default: 0)",
    )
    parser.add_argument(
        "--size",
        type=int,
        choices=(28, 64, 128, 224),
        help="expected spatial size; this validates the file and does not resize it",
    )
    parser.add_argument(
        "--as-rgb",
        action="store_true",
        help="convert grayscale 2D output to RGB or repeat 3D output to 3 channels",
    )
    parser.add_argument(
        "--mmap-mode",
        default=None,
        help="value forwarded to numpy.load, for example r or c (default: None)",
    )
    return parser


def write_fixture(path: Path, kind: str) -> None:
    """Write a deterministic, tiny, grayscale six-key fixture."""
    labels = np.array([[0], [1]], dtype=np.uint8)
    if kind == "2d":
        shape = (2, 28, 28)
    else:
        shape = (2, 28, 28, 28)
    values = np.arange(np.prod(shape), dtype=np.uint32).reshape(shape)
    images = (values % 256).astype(np.uint8)
    np.savez(
        path,
        train_images=images,
        train_labels=labels,
        val_images=images,
        val_labels=labels,
        test_images=images,
        test_labels=labels,
    )


def infer_kind(images: np.ndarray, requested: str) -> str:
    if requested != "auto":
        return requested
    if images.ndim == 3:
        return "2d"
    if images.ndim == 4:
        # Standard RGB 2D arrays end in three channels. A final singleton is
        # accepted as 2D only to provide a useful diagnostic below.
        if images.shape[-1] in (1, 3):
            return "2d"
        return "3d"
    raise ValidationError(
        f"cannot infer 2D/3D from image rank {images.ndim}; expected "
        "(N,H,W), (N,H,W,3), or (N,D,H,W); pass --kind explicitly if needed"
    )


def validate_images(images: np.ndarray, kind: str, size: Optional[int]) -> None:
    if not np.issubdtype(images.dtype, np.number):
        raise ValidationError(
            f"images must use a numeric dtype for pixel conversion; received {images.dtype}"
        )
    if images.ndim == 0 or images.shape[0] == 0:
        raise ValidationError("selected images array must have a non-zero sample dimension")

    if kind == "2d":
        if images.ndim == 3:
            spatial = images.shape[1:]
        elif images.ndim == 4 and images.shape[-1] == 3:
            spatial = images.shape[1:3]
        else:
            raise ValidationError(
                "2D images must have shape (N,H,W) or (N,H,W,3); "
                f"received {images.shape}"
            )
        allowed = SIZES_2D
    else:
        if images.ndim != 4:
            raise ValidationError(
                "3D images must have shape (N,D,H,W); "
                f"received {images.shape}"
            )
        spatial = images.shape[1:]
        if len(set(spatial)) != 1:
            raise ValidationError(
                "3D fixture must be cubic (D=H=W); " f"received spatial shape {spatial}"
            )
        allowed = SIZES_3D

    if len(set(spatial)) != 1:
        raise ValidationError(
            f"images must be square for this loader; received spatial shape {spatial}"
        )
    actual = int(spatial[0])
    if actual not in allowed:
        raise ValidationError(
            f"{kind} spatial size {actual} is not a MedMNIST size; "
            f"supported sizes are {list(allowed)}"
        )
    if size is not None:
        if size not in allowed:
            raise ValidationError(
                f"size={size} is invalid for {kind}; supported sizes are {list(allowed)}"
            )
        if actual != size:
            raise ValidationError(
                f"--size={size} does not match the NPZ spatial size {actual}; "
                "the script validates but does not resize"
            )


def load_and_report(
    path: Path,
    kind_request: str,
    split: str,
    index: int,
    size: Optional[int],
    as_rgb: bool,
    mmap_mode: Optional[str],
) -> None:
    if not path.is_file():
        raise ValidationError(
            f"NPZ file not found: {path}. Create the root/file first or pass "
            "--fixture 2d/3d; this script does not download data"
        )

    try:
        archive = np.load(path, mmap_mode=mmap_mode, allow_pickle=False)
    except (OSError, ValueError, EOFError, zipfile.BadZipFile) as exc:
        raise ValidationError(f"could not open NPZ {path}: {exc}") from exc
    if not isinstance(archive, np.lib.npyio.NpzFile):
        raise ValidationError(
            f"expected an NPZ archive at {path}; received a non-NPZ NumPy file"
        )

    with archive:
        missing = sorted(REQUIRED_KEYS.difference(archive.files))
        if missing:
            raise ValidationError(
                "NPZ is missing required members "
                f"{missing}; expected {sorted(REQUIRED_KEYS)}"
            )

        images = archive[f"{split}_images"]
        labels = archive[f"{split}_labels"]
        if images.shape[0] != labels.shape[0]:
            raise ValidationError(
                f"{split} image/label count mismatch: "
                f"{images.shape[0]} versus {labels.shape[0]}"
            )
        if labels.ndim != 2:
            raise ValidationError(
                f"{split}_labels must have shape (N,L), received {labels.shape}"
            )
        if not np.issubdtype(labels.dtype, np.number):
            raise ValidationError(
                f"{split}_labels must use a numeric dtype; received {labels.dtype}"
            )
        if index < 0 or index >= images.shape[0]:
            raise ValidationError(
                f"--index={index} is outside {split} range [0, {images.shape[0] - 1}]"
            )

        kind = infer_kind(images, kind_request)
        validate_images(images, kind, size)
        target = np.asarray(labels[index]).astype(int)
        raw = np.asarray(images[index])
        spatial = raw.shape[0:2] if kind == "2d" and raw.ndim == 3 else raw.shape
        actual_size = int(spatial[0])

        print(f"opened: {path}")
        print(f"keys: {sorted(archive.files)}")
        print(f"split: {split}")
        print(f"kind: {kind}")
        print(f"size: {actual_size}")
        print(f"mmap_mode: {mmap_mode!r}")
        print(f"images: shape={images.shape}, dtype={images.dtype}")
        print(f"labels: shape={labels.shape}, dtype={labels.dtype}")

        if kind == "2d":
            try:
                from PIL import Image
            except ImportError as exc:
                raise ValidationError(
                    "2D sample conversion requires Pillow; install Pillow or inspect "
                    "the NPZ arrays directly"
                ) from exc
            if raw.ndim == 3 and raw.shape[-1] == 1:
                raise ValidationError(
                    "2D singleton-channel images are not standard; store grayscale as "
                    "(N,H,W) or RGB as (N,H,W,3)"
                )
            try:
                image = Image.fromarray(raw)
                if as_rgb:
                    image = image.convert("RGB")
            except (TypeError, ValueError) as exc:
                raise ValidationError(
                    f"could not convert 2D sample to a Pillow image: {exc}"
                ) from exc
            print(
                "sample: image_type=PIL.Image.Image "
                f"mode={image.mode} size={image.size} "
                f"array_shape={np.asarray(image).shape} dtype={np.asarray(image).dtype}"
            )
        else:
            normalized = raw.astype(np.float32, copy=False) / 255.0
            channels = 3 if as_rgb else 1
            image = np.stack([normalized] * channels, axis=0)
            print(
                "sample: image_type=numpy.ndarray "
                f"shape={image.shape} dtype={image.dtype} "
                f"range=[{float(image.min()):.6f}, {float(image.max()):.6f}]"
            )
        print(f"target: shape={target.shape} dtype={target.dtype} values={target.tolist()}")
        print("status: OK (local read only; no download performed)")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.fixture:
            if args.kind != "auto" and args.kind != args.fixture:
                raise ValidationError(
                    f"--fixture {args.fixture} conflicts with --kind {args.kind}"
                )
            with tempfile.TemporaryDirectory(prefix="medmnist-fixture-") as directory:
                path = Path(directory) / f"fixture_{args.fixture}.npz"
                write_fixture(path, args.fixture)
                load_and_report(
                    path,
                    args.fixture,
                    args.split,
                    args.index,
                    args.size,
                    args.as_rgb,
                    args.mmap_mode,
                )
        else:
            load_and_report(
                args.npz,
                args.kind,
                args.split,
                args.index,
                args.size,
                args.as_rgb,
                args.mmap_mode,
            )
    except ValidationError as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
