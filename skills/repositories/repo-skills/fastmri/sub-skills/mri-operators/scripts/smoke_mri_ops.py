#!/usr/bin/env python3
"""Tiny CPU smoke checks for fastMRI MRI tensor operators."""

import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run tiny CPU checks for fastMRI complex_abs, centered FFT/IFFT, "
            "RSS coil combine, and center crop."
        )
    )
    parser.add_argument("--height", type=int, default=8, help="Spatial height for the test tensor.")
    parser.add_argument("--width", type=int, default=10, help="Spatial width for the test tensor.")
    parser.add_argument("--coils", type=int, default=4, help="Number of coils for the RSS check.")
    parser.add_argument(
        "--crop-height",
        type=int,
        default=4,
        help="Center-crop height; must be positive and no larger than --height.",
    )
    parser.add_argument(
        "--crop-width",
        type=int,
        default=6,
        help="Center-crop width; must be positive and no larger than --width.",
    )
    return parser.parse_args()


def require_positive(name, value):
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def main():
    args = parse_args()
    for name in ("height", "width", "coils", "crop_height", "crop_width"):
        require_positive(name, getattr(args, name))
    if args.crop_height > args.height or args.crop_width > args.width:
        raise ValueError("crop dimensions must be no larger than the test tensor dimensions")

    try:
        import torch
        import fastmri
        from fastmri.data import transforms
    except ModuleNotFoundError as exc:
        if exc.name == "requests":
            raise SystemExit(
                "fastmri.data requires the 'requests' package in this checkout; "
                "install it in the active environment before running transform checks."
            ) from exc
        raise

    height = args.height
    width = args.width
    coils = args.coils
    crop_shape = (args.crop_height, args.crop_width)

    values = torch.arange(height * width * 2, dtype=torch.float32).reshape(1, height, width, 2)

    magnitude = fastmri.complex_abs(values)
    assert magnitude.shape == (1, height, width), magnitude.shape

    image = fastmri.ifft2c(values)
    round_trip = fastmri.fft2c(image)
    assert image.shape == values.shape, image.shape
    assert round_trip.shape == values.shape, round_trip.shape
    if not torch.allclose(round_trip, values, atol=1e-5, rtol=1e-5):
        raise AssertionError("fft2c(ifft2c(x)) did not round-trip within tolerance")

    coil_images = torch.ones(coils, height, width, dtype=torch.float32)
    rss = fastmri.rss(coil_images, dim=0)
    assert rss.shape == (height, width), rss.shape
    assert torch.allclose(rss, torch.full((height, width), coils**0.5)), rss

    cropped = transforms.center_crop(rss, crop_shape)
    assert cropped.shape == crop_shape, cropped.shape

    print("fastMRI MRI operator smoke checks passed")
    print(f"complex_abs: {tuple(magnitude.shape)}")
    print(f"fft2c/ifft2c: {tuple(round_trip.shape)}")
    print(f"rss dim=0: {tuple(rss.shape)}")
    print(f"center_crop: {tuple(cropped.shape)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"smoke_mri_ops failed: {exc}", file=sys.stderr)
        sys.exit(1)
