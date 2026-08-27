#!/usr/bin/env python3
"""Run deterministic SimpleITK filtering and segmentation smoke checks.

The helper creates tiny synthetic images, applies common filtering and
segmentation workflows, and prints a JSON summary. It performs no file IO,
network access, destructive writes, or viewer calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny SimpleITK filtering/segmentation smoke checks and print JSON."
    )
    parser.add_argument(
        "--mode",
        choices=("all", "threshold", "connected", "fast-marching"),
        default="all",
        help="Workflow to run. The default runs every bounded smoke check.",
    )
    parser.add_argument(
        "--size",
        type=positive_int,
        default=64,
        help="Synthetic 2D image width and height.",
    )
    parser.add_argument(
        "--sigma",
        type=float,
        default=1.25,
        help="Gaussian smoothing sigma in physical units.",
    )
    parser.add_argument(
        "--histogram-bins",
        type=positive_int,
        default=64,
        help="Histogram bins for Otsu thresholding.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser.parse_args(argv)


def import_simpleitk() -> Any:
    try:
        import SimpleITK as sitk  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local environment
        raise SystemExit(f"SimpleITK import failed: {exc}") from exc
    return sitk


def make_synthetic_image(sitk: Any, size: int) -> Any:
    image_size = [size, size]
    center = [size / 2.0, size / 2.0]
    blob_sigma = [max(size / 7.0, 1.0), max(size / 9.0, 1.0)]
    faint_sigma = [max(size / 13.0, 1.0), max(size / 13.0, 1.0)]
    faint_center = [size * 0.28, size * 0.72]

    blob = sitk.GaussianSource(sitk.sitkFloat32, image_size, blob_sigma, center, 180.0)
    faint_blob = sitk.GaussianSource(sitk.sitkFloat32, image_size, faint_sigma, faint_center, 45.0)
    image = blob + faint_blob + 10.0
    image.SetSpacing([0.8, 1.3])
    return image


def image_statistics(sitk: Any, image: Any) -> dict[str, Any]:
    stats = sitk.StatisticsImageFilter()
    stats.Execute(image)
    return {
        "size": list(image.GetSize()),
        "spacing": [float(value) for value in image.GetSpacing()],
        "pixel_id": image.GetPixelIDTypeAsString(),
        "minimum": float(stats.GetMinimum()),
        "maximum": float(stats.GetMaximum()),
        "mean": float(stats.GetMean()),
        "variance": float(stats.GetVariance()),
    }


def label_summary(sitk: Any, mask: Any) -> dict[str, Any]:
    labels = sitk.ConnectedComponent(sitk.Cast(mask, sitk.sitkUInt8))
    shape = sitk.LabelShapeStatisticsImageFilter()
    shape.SetComputeFeretDiameter(False)
    shape.SetComputeOrientedBoundingBox(False)
    shape.Execute(labels)

    objects = []
    for label in shape.GetLabels():
        objects.append(
            {
                "label": int(label),
                "pixels": int(shape.GetNumberOfPixels(label)),
                "physical_size": float(shape.GetPhysicalSize(label)),
                "centroid": [round(float(value), 4) for value in shape.GetCentroid(label)],
                "bounding_box": [int(value) for value in shape.GetBoundingBox(label)],
            }
        )

    return {
        "label_count": int(shape.GetNumberOfLabels()),
        "objects": objects,
    }


def threshold_workflow(sitk: Any, args: argparse.Namespace) -> dict[str, Any]:
    image = make_synthetic_image(sitk, args.size)
    smoothed = sitk.SmoothingRecursiveGaussian(image, [args.sigma] * image.GetDimension())

    otsu = sitk.OtsuThresholdImageFilter()
    otsu.SetInsideValue(0)
    otsu.SetOutsideValue(1)
    otsu.SetNumberOfHistogramBins(args.histogram_bins)
    otsu_mask = otsu.Execute(smoothed)
    threshold = float(otsu.GetThreshold())

    smoothed_stats = image_statistics(sitk, smoothed)
    binary_mask = sitk.BinaryThreshold(smoothed, threshold, smoothed_stats["maximum"], 1, 0)

    return {
        "mode": "threshold",
        "input": image_statistics(sitk, image),
        "smoothed": smoothed_stats,
        "otsu_threshold": threshold,
        "otsu_labels": label_summary(sitk, otsu_mask),
        "binary_threshold_labels": label_summary(sitk, binary_mask),
    }


def connected_workflow(sitk: Any, args: argparse.Namespace) -> dict[str, Any]:
    image = make_synthetic_image(sitk, args.size)
    smoothed = sitk.SmoothingRecursiveGaussian(image, [args.sigma] * image.GetDimension())

    otsu = sitk.OtsuThresholdImageFilter()
    otsu.SetInsideValue(0)
    otsu.SetOutsideValue(1)
    otsu.SetNumberOfHistogramBins(args.histogram_bins)
    otsu.Execute(smoothed)
    threshold = float(otsu.GetThreshold())
    stats = image_statistics(sitk, smoothed)

    seed = [args.size // 2, args.size // 2]
    segmenter = sitk.ConnectedThresholdImageFilter()
    segmenter.SetLower(threshold)
    segmenter.SetUpper(stats["maximum"])
    segmenter.SetReplaceValue(1)
    segmenter.AddSeed(seed)
    mask = segmenter.Execute(smoothed)

    return {
        "mode": "connected",
        "seed": seed,
        "seed_intensity": float(smoothed.GetPixel(*seed)),
        "lower": threshold,
        "upper": stats["maximum"],
        "smoothed": stats,
        "connected_labels": label_summary(sitk, mask),
    }


def fast_marching_workflow(sitk: Any, args: argparse.Namespace) -> dict[str, Any]:
    image = make_synthetic_image(sitk, args.size)
    smoothed = sitk.SmoothingRecursiveGaussian(image, [args.sigma] * image.GetDimension())

    gradient = sitk.GradientMagnitudeRecursiveGaussian(smoothed, sigma=max(args.sigma, 0.5))
    sigmoid = sitk.SigmoidImageFilter()
    sigmoid.SetOutputMinimum(0.05)
    sigmoid.SetOutputMaximum(1.0)
    sigmoid.SetAlpha(-0.15)
    sigmoid.SetBeta(12.0)
    speed = sigmoid.Execute(gradient)

    seed = [args.size // 2, args.size // 2]
    stopping_time = float(max(args.size, 16))
    time_threshold = stopping_time * 0.42

    marcher = sitk.FastMarchingImageFilter()
    try:
        marcher.AddTrialPoint([seed[0], seed[1], 0.0])
    except TypeError:
        marcher.AddTrialPoint([seed[0], seed[1]])
    marcher.SetStoppingValue(stopping_time)
    arrival = marcher.Execute(speed)
    mask = sitk.BinaryThreshold(arrival, 0.0, time_threshold, 1, 0)

    return {
        "mode": "fast-marching",
        "seed": seed,
        "stopping_time": stopping_time,
        "time_threshold": time_threshold,
        "speed": image_statistics(sitk, speed),
        "arrival": image_statistics(sitk, arrival),
        "mask_labels": label_summary(sitk, mask),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    sitk = import_simpleitk()

    workflows = {
        "threshold": threshold_workflow,
        "connected": connected_workflow,
        "fast-marching": fast_marching_workflow,
    }
    if args.mode == "all":
        result: dict[str, Any] = {
            name: workflow(sitk, args) for name, workflow in workflows.items()
        }
        result["mode"] = "all"
    else:
        result = workflows[args.mode](sitk, args)

    version_fn = getattr(sitk, "Version_VersionString", None)
    result["simpleitk_version"] = version_fn() if callable(version_fn) else "unknown"
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
