#!/usr/bin/env python3
"""Convert LoveDA 0..7 source labels to GeoSeg train labels.

The source encoding is 0=void/ignore and 1..7=classes.  GeoSeg stores
1..7 as 0..6 and keeps source 0 as ignore label 7.  A color copy is written
beside the indexed mask with the suffix ``_rgb``.
"""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

PALETTE = np.asarray(
    [[255, 255, 255], [255, 0, 0], [255, 255, 0], [0, 0, 255],
     [159, 129, 183], [0, 255, 0], [255, 195, 128]], dtype=np.uint8
)
IGNORE = 7


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mask-dir", required=True, help="Directory of source PNG masks")
    p.add_argument("--output-mask-dir", required=True, help="Directory for indexed PNG masks")
    p.add_argument("--overwrite", action="store_true", help="Replace existing outputs")
    return p


def convert(values: np.ndarray) -> np.ndarray:
    """Return the GeoSeg indexed encoding, rejecting unsupported labels."""
    if values.ndim != 2:
        raise ValueError("LoveDA masks must be single-channel grayscale PNGs")
    labels = set(np.unique(values).tolist())
    unsupported = labels.difference(range(8))
    if unsupported:
        raise ValueError("unsupported LoveDA label values: " + ", ".join(map(str, sorted(unsupported))))
    out = values.astype(np.uint8, copy=True)
    out[out == 0] = 8
    out -= 1
    return out


def colorize(indexed: np.ndarray) -> np.ndarray:
    rgb = np.zeros(indexed.shape + (3,), dtype=np.uint8)
    for label, color in enumerate(PALETTE):
        rgb[indexed == label] = color
    # Ignore (7) remains black, making an accidental training use visible.
    return rgb


def atomic_save(array: np.ndarray, path: Path, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError("refusing to overwrite: {} (use --overwrite)".format(path))
    fd, tmp = tempfile.mkstemp(prefix=".geoseg-", suffix=path.suffix, dir=str(path.parent))
    os.close(fd)
    tmp_path = Path(tmp)
    try:
        Image.fromarray(array).save(str(tmp_path), format="PNG")
        os.replace(str(tmp_path), str(path))
    finally:
        tmp_path.unlink(missing_ok=True)


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    source = Path(args.mask_dir).expanduser()
    output = Path(args.output_mask_dir).expanduser()
    if not source.is_dir():
        raise SystemExit("mask directory does not exist: {}".format(source))
    files = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() == ".png")
    if not files:
        raise SystemExit("no PNG masks found in {}".format(source))
    # Validate every input before writing any output, so bad labels cannot leave
    # a deceptively complete-looking conversion.
    converted = []
    for path in files:
        with Image.open(path) as image:
            converted.append((path, convert(np.asarray(image.convert("L")))))
    for path, indexed in converted:
        name = path.stem + ".png"
        atomic_save(indexed, output / name, args.overwrite)
        atomic_save(colorize(indexed), Path(str(output) + "_rgb") / name, args.overwrite)
    print("converted {} LoveDA masks to {} (indexed) and {} (RGB)".format(
        len(converted), output, Path(str(output) + "_rgb")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
