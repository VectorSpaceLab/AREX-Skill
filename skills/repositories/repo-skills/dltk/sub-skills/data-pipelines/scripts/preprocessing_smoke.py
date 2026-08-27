#!/usr/bin/env python3
"""Bounded, dependency-light checks for DLTK-style preprocessing.

This intentionally uses synthetic NumPy arrays instead of importing the legacy
DLTK implementation. It checks the documented numerical contracts and a safe
center-crop/pad adaptation that works with current NumPy and channel-last data.
It never reads or writes a dataset.
"""
from __future__ import print_function

import argparse
import sys

import numpy as np


def whitening(image):
    image = np.asarray(image, dtype=np.float32)
    mean = np.mean(image)
    std = np.std(image)
    return (image - mean) / std if std > 0 else image * 0.0


def normalise_zero_one(image):
    image = np.asarray(image, dtype=np.float32)
    minimum = np.min(image)
    maximum = np.max(image)
    if maximum > minimum:
        return (image - minimum) / (maximum - minimum)
    return image * 0.0


def normalise_one_one(image):
    return normalise_zero_one(image) * 2.0 - 1.0


def center_crop_or_pad(image, spatial_size, pad_value=0.0):
    """Safe channel-last equivalent of the legacy crop/pad intent."""
    image = np.asarray(image)
    spatial_size = tuple(int(x) for x in spatial_size)
    rank = len(spatial_size)
    if image.ndim not in (rank, rank + 1):
        raise ValueError("expected spatial rank or spatial rank + channel")

    slices = []
    pad_width = []
    for current, target in zip(image.shape[:rank], spatial_size):
        if current >= target:
            start = (current - target) // 2
            slices.append(slice(start, start + target))
            pad_width.append((0, 0))
        else:
            before = (target - current) // 2
            after = target - current - before
            slices.append(slice(0, current))
            pad_width.append((before, after))
    if image.ndim == rank + 1:
        slices.append(slice(None))
        pad_width.append((0, 0))

    cropped = image[tuple(slices)]
    return np.pad(cropped, pad_width, mode="constant",
                  constant_values=pad_value)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def run(seed):
    rng = np.random.RandomState(seed)

    varying = np.arange(3 * 4 * 5, dtype=np.float32).reshape(3, 4, 5)
    white = whitening(varying)
    check(white.dtype == np.float32, "whitening must return float32")
    check(abs(float(np.mean(white))) < 1e-6, "whitening mean is not zero")
    check(abs(float(np.std(white)) - 1.0) < 1e-6,
          "whitening standard deviation is not one")

    constant = np.full((2, 2), 7, dtype=np.int16)
    check(np.array_equal(whitening(constant), np.zeros((2, 2), np.float32)),
          "constant whitening must be zero")
    check(np.array_equal(normalise_zero_one(constant),
                         np.zeros((2, 2), np.float32)),
          "constant zero-one normalization must be zero")
    check(np.array_equal(normalise_one_one(constant),
                         -np.ones((2, 2), np.float32)),
          "constant one-one normalization must be minus one")

    norm = normalise_zero_one(varying)
    check(float(np.min(norm)) == 0.0 and float(np.max(norm)) == 1.0,
          "zero-one normalization range is wrong")
    one_one = normalise_one_one(varying)
    check(float(np.min(one_one)) == -1.0 and float(np.max(one_one)) == 1.0,
          "one-one normalization range is wrong")

    # Exercise both crop and pad with a final channel dimension. The source
    # examples use [spatial..., channels] and the channel must not be padded.
    image = rng.randn(3, 4, 5, 2).astype(np.float32)
    padded = center_crop_or_pad(image, (5, 2, 6), pad_value=-3.0)
    cropped = center_crop_or_pad(image, (2, 2, 3), pad_value=-3.0)
    check(padded.shape == (5, 2, 6, 2), "padded shape is wrong")
    check(cropped.shape == (2, 2, 3, 2), "cropped shape is wrong")
    check(np.all(padded[0, :, :, :] == -3.0),
          "symmetric padding did not use the requested value")
    check(np.array_equal(cropped.shape[-1:], image.shape[-1:]),
          "crop/pad changed the channel count")

    # A deliberately tiny synchronized image/label check catches accidental
    # independent spatial transforms without depending on scipy or TensorFlow.
    label = np.arange(3 * 4 * 5).reshape(3, 4, 5) % 2
    multimodal = np.stack([label, label + 10], axis=-1).astype(np.float32)
    flipped_image = np.flip(multimodal, axis=1)
    flipped_label = np.flip(label, axis=1)
    check(np.array_equal(flipped_image[..., 0].astype(np.int64), flipped_label),
          "synchronized spatial transform lost image/label alignment")

    print("preprocessing smoke passed (seed={})".format(seed))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run bounded synthetic DLTK preprocessing checks.")
    parser.add_argument("--seed", type=int, default=17,
                        help="deterministic seed for the tiny fixture")
    args = parser.parse_args(argv)
    try:
        return run(args.seed)
    except (AssertionError, ValueError) as exc:
        print("preprocessing smoke failed: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
