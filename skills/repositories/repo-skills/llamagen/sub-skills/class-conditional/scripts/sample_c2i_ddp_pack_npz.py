#!/usr/bin/env python3
"""Package numbered PNG samples into a c2i evaluation .npz.

The native c2i DDP sampler writes PNG files directly under its generated
sample folder:

  sample_dir/000000.png
  sample_dir/000001.png
  ...

For convenience, this helper also accepts a sample root that contains an
``images/`` subdirectory; in that case the PNGs are read from
``sample_dir/images`` and the default output remains ``sample_dir.npz``.
The output stores images under ``arr_0`` as NHWC uint8 RGB arrays.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def resolve_image_dir(sample_root: Path, images_subdir: str | None) -> Path:
    """Return the directory that should contain zero-padded PNG files."""
    if images_subdir:
        image_dir = sample_root / images_subdir
    elif (sample_root / "000000.png").is_file():
        image_dir = sample_root
    elif (sample_root / "images").is_dir():
        image_dir = sample_root / "images"
    else:
        image_dir = sample_root
    if not image_dir.is_dir():
        raise NotADirectoryError(f"sample image directory does not exist: {image_dir}")
    return image_dir


def pack_sample_folder(image_dir: Path, num: int) -> np.ndarray:
    samples = []
    for index in range(num):
        path = image_dir / f"{index:06d}.png"
        if not path.is_file():
            raise FileNotFoundError(f"missing sample image: {path}")
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            sample = np.asarray(rgb, dtype=np.uint8)
        if sample.ndim != 3 or sample.shape[-1] != 3:
            raise ValueError(f"expected RGB image, got shape {sample.shape} from {path}")
        samples.append(sample)
    stacked = np.stack(samples, axis=0)
    if stacked.dtype != np.uint8:
        stacked = stacked.astype(np.uint8, copy=False)
    return stacked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample_dir_arg", nargs="?", help="sample folder or sample root containing numbered PNGs")
    parser.add_argument("--sample-dir", dest="sample_dir_opt", help="sample folder or sample root containing numbered PNGs")
    parser.add_argument("--images-subdir", default=None, help="optional subdirectory inside sample_dir that contains numbered PNGs")
    parser.add_argument("--num", type=int, default=50_000, help="number of PNG files to package")
    parser.add_argument("--output", type=str, default=None, help="output .npz path; defaults to <sample_dir>.npz")
    args = parser.parse_args()

    sample_dir_value = args.sample_dir_opt or args.sample_dir_arg
    if not sample_dir_value:
        parser.error("provide SAMPLE_DIR or --sample-dir")

    sample_root = Path(sample_dir_value).expanduser()
    if not sample_root.is_dir():
        raise NotADirectoryError(f"sample directory does not exist: {sample_root}")

    image_dir = resolve_image_dir(sample_root, args.images_subdir)
    samples = pack_sample_folder(image_dir, args.num)
    output = Path(args.output).expanduser() if args.output else Path(f"{sample_root}.npz")
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez(output, arr_0=samples)
    print(f"Saved {output} with arr_0 shape {samples.shape} from {image_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
