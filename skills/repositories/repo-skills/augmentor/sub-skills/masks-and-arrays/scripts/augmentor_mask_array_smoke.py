#!/usr/bin/env python3
"""Tiny Augmentor DataPipeline smoke for grouped original+mask arrays."""

import argparse
import random

import numpy as np
import Augmentor


def build_group(height=16, width=16):
    """Create one synthetic RGB image and one monochrome mask."""
    yy, xx = np.mgrid[0:height, 0:width]
    image = np.stack(
        [
            (xx * 11) % 256,
            (yy * 17) % 256,
            ((xx + yy) * 7) % 256,
        ],
        axis=-1,
    ).astype(np.uint8)
    mask = (((xx >= width // 4) & (xx < 3 * width // 4)) & (yy >= height // 4)).astype(np.uint8) * 255
    return [image, mask.astype(np.uint8)]


def main():
    parser = argparse.ArgumentParser(description="Run a tiny in-memory Augmentor mask DataPipeline smoke check.")
    parser.add_argument("--samples", type=int, default=2, help="number of augmented groups to sample")
    args = parser.parse_args()

    if args.samples < 1:
        raise SystemExit("--samples must be at least 1")

    random.seed(0)
    np.random.seed(0)

    input_group = build_group()
    expected_group_count = len(input_group)
    expected_label = "synthetic-mask"

    pipeline = Augmentor.DataPipeline([input_group], [expected_label])
    pipeline.rotate(probability=1, max_left_rotation=5, max_right_rotation=5)

    batch, labels = pipeline.sample(args.samples)

    assert len(batch) == args.samples, (len(batch), args.samples)
    assert len(labels) == args.samples, (len(labels), args.samples)
    assert all(label == expected_label for label in labels), labels

    shape_rows = []
    for sample_index, group in enumerate(batch):
        assert len(group) == expected_group_count, (len(group), expected_group_count)
        image, mask = group
        assert isinstance(image, np.ndarray), type(image)
        assert isinstance(mask, np.ndarray), type(mask)
        assert image.shape[:2] == mask.shape[:2], (image.shape, mask.shape)
        shape_rows.append([tuple(arr.shape) for arr in group])
        print(f"sample {sample_index}: shapes {shape_rows[-1]}, label {labels[sample_index]}")

    print(f"ok: {len(batch)} grouped samples, group_count={expected_group_count}, labels={labels}")


if __name__ == "__main__":
    main()
