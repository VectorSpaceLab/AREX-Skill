#!/usr/bin/env python3
"""Generate a tiny headless contact sheet for representative imgaug augmenters.

This adapts the source repository's manual visual-check idea into a safe helper:
no GUI, no network, small built-in sample image, and explicit output path.

Example:
    python sub-skills/augmentation-pipelines/scripts/generate_augmentation_contact_sheet.py --output contact_sheet.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a small imgaug augmentation contact sheet.")
    parser.add_argument("--output", default="imgaug_contact_sheet.png", help="PNG path to write.")
    parser.add_argument("--size", type=int, default=96, help="Square sample image size in pixels.")
    parser.add_argument("--cols", type=int, default=4, help="Number of columns in the output grid.")
    args = parser.parse_args()

    import imageio.v2 as imageio
    import imgaug as ia
    import imgaug.augmenters as iaa

    image = ia.data.quokka_square(size=(args.size, args.size))
    augmenters = [
        iaa.Identity(name="identity"),
        iaa.Fliplr(1.0, name="fliplr"),
        iaa.Affine(rotate=15, name="affine-rotate"),
        iaa.CropAndPad(percent=(-0.08, 0.08), pad_cval=128, name="crop-pad"),
        iaa.GaussianBlur(1.0, name="gaussian-blur"),
        iaa.Add(25, name="add"),
        iaa.LinearContrast(1.5, name="linear-contrast"),
        iaa.Grayscale(alpha=0.8, name="grayscale"),
    ]
    images = [aug(image=image) for aug in augmenters]
    grid = ia.draw_grid(images, cols=args.cols)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    imageio.imwrite(output, np.asarray(grid, dtype=np.uint8))
    print(f"wrote {output} with {len(images)} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
