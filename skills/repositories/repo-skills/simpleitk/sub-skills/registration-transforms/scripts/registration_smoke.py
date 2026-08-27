#!/usr/bin/env python3
"""Deterministic SimpleITK registration/resampling smoke test.

Creates a tiny synthetic fixed image, makes a translated moving image, recovers
an approximate translation with ImageRegistrationMethod, resamples moving onto
fixed, and prints a JSON summary. No files are read or written.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from contextlib import contextmanager
from typing import Any, Iterable


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a deterministic tiny SimpleITK translation registration smoke test."
    )
    parser.add_argument("--size", type=int, default=64, help="Square image size in pixels. Default: 64.")
    parser.add_argument("--shift-x", type=float, default=4.0, help="Synthetic fixed-to-moving x translation. Default: 4.0.")
    parser.add_argument("--shift-y", type=float, default=-3.0, help="Synthetic fixed-to-moving y translation. Default: -3.0.")
    parser.add_argument("--seed", type=int, default=42, help="Metric sampling seed. Default: 42.")
    parser.add_argument("--sampling", type=float, default=0.35, help="Random metric sampling fraction. Default: 0.35.")
    parser.add_argument("--iterations", type=int, default=80, help="Optimizer iteration limit. Default: 80.")
    parser.add_argument("--single-thread", action="store_true", help="Temporarily force one SimpleITK thread when supported.")
    return parser


@contextmanager
def _single_thread_if_requested(sitk: Any, enabled: bool):
    if not enabled:
        yield False
        return

    getter = getattr(sitk, "ProcessObject_GetGlobalDefaultNumberOfThreads", None)
    setter = getattr(sitk, "ProcessObject_SetGlobalDefaultNumberOfThreads", None)
    if getter is None or setter is None:
        process_object = getattr(sitk, "ProcessObject", None)
        getter = getattr(process_object, "GetGlobalDefaultNumberOfThreads", None)
        setter = getattr(process_object, "SetGlobalDefaultNumberOfThreads", None)

    if getter is None or setter is None:
        yield False
        return

    previous = getter()
    setter(1)
    try:
        yield True
    finally:
        setter(previous)


def _translation_values(transform: Any) -> tuple[float, ...]:
    if hasattr(transform, "Downcast"):
        transform = transform.Downcast()
    if hasattr(transform, "GetOffset"):
        return tuple(float(value) for value in transform.GetOffset())
    return tuple(float(value) for value in transform.GetParameters())


def _rms(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        return 0.0
    return math.sqrt(sum(value * value for value in values) / len(values))


def run(args: argparse.Namespace) -> dict[str, Any]:
    try:
        import SimpleITK as sitk
    except ImportError as exc:
        return {"ok": False, "error": "SimpleITK is not importable", "detail": str(exc)}

    if args.size < 24:
        return {"ok": False, "error": "--size must be at least 24"}
    if not (0.0 < args.sampling <= 1.0):
        return {"ok": False, "error": "--sampling must be in (0, 1]"}

    expected = (float(args.shift_x), float(args.shift_y))

    with _single_thread_if_requested(sitk, args.single_thread) as single_thread_applied:
        fixed = sitk.GaussianSource(
            sitk.sitkFloat32,
            [args.size, args.size],
            sigma=[args.size / 10.0, args.size / 12.0],
            mean=[args.size * 0.45, args.size * 0.55],
            scale=1.0,
        )
        fixed += 0.65 * sitk.GaussianSource(
            sitk.sitkFloat32,
            [args.size, args.size],
            sigma=[args.size / 14.0, args.size / 11.0],
            mean=[args.size * 0.68, args.size * 0.28],
            scale=1.0,
        )

        fixed_to_moving = sitk.TranslationTransform(2, expected)
        moving = sitk.Resample(
            fixed,
            fixed,
            transform=fixed_to_moving.GetInverse(),
            interpolator=sitk.sitkLinear,
            defaultPixelValue=0.0,
        )

        registration = sitk.ImageRegistrationMethod()
        registration.SetMetricAsMeanSquares()
        registration.SetMetricSamplingStrategy(registration.RANDOM)
        registration.SetMetricSamplingPercentage(float(args.sampling), int(args.seed))
        registration.SetOptimizerAsRegularStepGradientDescent(
            learningRate=1.0,
            minStep=1e-4,
            numberOfIterations=int(args.iterations),
            relaxationFactor=0.5,
            gradientMagnitudeTolerance=1e-8,
        )
        registration.SetInitialTransform(sitk.TranslationTransform(2))
        registration.SetInterpolator(sitk.sitkLinear)

        metric_trace: list[float] = []
        registration.AddCommand(
            sitk.sitkIterationEvent,
            lambda: metric_trace.append(float(registration.GetMetricValue())),
        )

        out_tx = registration.Execute(fixed, moving)
        recovered = _translation_values(out_tx)
        resampled = sitk.Resample(
            moving,
            fixed,
            transform=out_tx,
            interpolator=sitk.sitkLinear,
            defaultPixelValue=0.0,
        )
        difference = sitk.Abs(fixed - resampled)
        stats = sitk.StatisticsImageFilter()
        stats.Execute(difference)

    parameter_error = tuple(recovered[index] - expected[index] for index in range(2))

    return {
        "ok": True,
        "simpleitk_version": str(sitk.Version()).splitlines()[0],
        "image_size": [args.size, args.size],
        "expected_fixed_to_moving_translation": list(expected),
        "recovered_translation": list(recovered),
        "translation_error": list(parameter_error),
        "translation_rmse": _rms(parameter_error),
        "metric_value": float(registration.GetMetricValue()),
        "iterations": int(registration.GetOptimizerIteration()),
        "metric_trace_length": len(metric_trace),
        "stop_condition": registration.GetOptimizerStopConditionDescription(),
        "mean_absolute_resample_difference": float(stats.GetMean()),
        "max_absolute_resample_difference": float(stats.GetMaximum()),
        "single_thread_requested": bool(args.single_thread),
        "single_thread_applied": bool(single_thread_applied),
        "elastix_available": hasattr(sitk, "ElastixImageFilter"),
        "transformix_available": hasattr(sitk, "TransformixImageFilter"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    summary = run(args)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
