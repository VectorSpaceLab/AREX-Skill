#!/usr/bin/env python3
"""Validate a NanoTrackV3 profile/throughput plan without running the model."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from typing import Any


TEMPLATE_SHAPE = (1, 3, 127, 127)
SEARCH_SHAPE = (1, 3, 255, 255)


def parse_shape(text: str) -> tuple[int, int, int, int]:
    normalized = text.lower().replace("x", ",")
    parts = [part.strip() for part in normalized.split(",") if part.strip()]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            f"expected four NCHW integers, got {text!r}"
        )
    try:
        values = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"non-integer shape {text!r}") from exc
    if any(value <= 0 for value in values):
        raise argparse.ArgumentTypeError(f"shape values must be positive: {text!r}")
    return values  # type: ignore[return-value]


def positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected integer, got {text!r}") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return value


def nonnegative_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected integer, got {text!r}") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("value must be nonnegative")
    return value


def positive_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected number, got {text!r}") from exc
    if not 0.0 < value < float("inf"):
        raise argparse.ArgumentTypeError("value must be finite and positive")
    return value


def nonnegative_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected number, got {text!r}") from exc
    if not 0.0 <= value < float("inf"):
        raise argparse.ArgumentTypeError("value must be finite and nonnegative")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "No-run validator for NanoTrackV3 MAC/parameter and cached-template "
            "throughput methodology."
        )
    )
    parser.add_argument("--template-shape", type=parse_shape, default=TEMPLATE_SHAPE)
    parser.add_argument("--search-shape", type=parse_shape, default=SEARCH_SHAPE)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--timer", choices=("wall", "cuda-event"), default="wall")
    parser.add_argument(
        "--synchronize",
        action="store_true",
        help="Declare synchronization around each CUDA timed region.",
    )
    parser.add_argument("--warmup", type=nonnegative_int, default=100)
    parser.add_argument("--iterations", type=positive_int, default=1000)
    parser.add_argument("--repeats", type=positive_int, default=5)
    parser.add_argument("--num-threads", type=positive_int, default=1)
    parser.add_argument(
        "--elapsed-seconds",
        nargs="+",
        type=positive_float,
        help="Completed per-repeat durations to summarize; no model is run.",
    )
    parser.add_argument("--macs", type=nonnegative_float, help="Optional tool-native MAC count.")
    parser.add_argument("--params", type=nonnegative_float, help="Optional parameter count.")
    parser.add_argument("--profile-tool", help="Tool/version used for --macs/--params.")
    parser.add_argument(
        "--template-in-timed-region",
        action="store_true",
        help="Declare that template initialization is included in every duration.",
    )
    parser.add_argument("--include-preprocess", action="store_true")
    parser.add_argument("--include-postprocess", action="store_true")
    parser.add_argument("--include-transfers", action="store_true")
    parser.add_argument(
        "--allow-noncanonical-shapes",
        action="store_true",
        help="Treat shape changes as a variant plan rather than an error.",
    )
    parser.add_argument("--json-indent", type=nonnegative_int, default=2)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []

    for label, found, expected in (
        ("template", args.template_shape, TEMPLATE_SHAPE),
        ("search", args.search_shape, SEARCH_SHAPE),
    ):
        if found != expected:
            message = f"{label} shape is {list(found)}, canonical NanoTrackV3 shape is {list(expected)}"
            if args.allow_noncanonical_shapes:
                warnings.append(message + "; report this as a separate variant contract")
            else:
                errors.append(message)

    if args.device == "cpu" and args.timer == "cuda-event":
        errors.append("cuda-event timing requires --device cuda")
    if args.device == "cuda" and not args.synchronize:
        errors.append(
            "CUDA timing requires --synchronize so asynchronous kernels finish inside each timed region"
        )
    if args.device == "cpu" and args.synchronize:
        warnings.append("--synchronize has no CUDA timing effect on a CPU plan")
    if args.warmup == 0:
        warnings.append("zero warmup is valid for a tiny smoke but weak for a reported benchmark")
    if (args.macs is None) != (args.params is None):
        warnings.append("reporting only one of MACs/parameters can make profile comparisons ambiguous")
    if (args.macs is not None or args.params is not None) and not args.profile_tool:
        errors.append("--profile-tool is required when --macs or --params is supplied")

    throughput_summary: dict[str, Any] | None = None
    if args.elapsed_seconds:
        throughputs = [args.iterations / elapsed for elapsed in args.elapsed_seconds]
        latencies_ms = [elapsed * 1000.0 / args.iterations for elapsed in args.elapsed_seconds]
        if len(args.elapsed_seconds) != args.repeats:
            warnings.append(
                f"received {len(args.elapsed_seconds)} durations but --repeats is {args.repeats}"
            )
        throughput_summary = {
            "samples": len(args.elapsed_seconds),
            "elapsed_seconds": args.elapsed_seconds,
            "search_calls_per_second": {
                "median": statistics.median(throughputs),
                "min": min(throughputs),
                "max": max(throughputs),
            },
            "latency_ms_per_search_call": {
                "median": statistics.median(latencies_ms),
                "min": min(latencies_ms),
                "max": max(latencies_ms),
            },
        }

    if args.template_in_timed_region:
        boundary = "template initialization plus search calls"
        warnings.append(
            "throughput denominator is still search calls; report template initialization separately when possible"
        )
    else:
        boundary = "cached-template search calls"

    if not args.include_preprocess or not args.include_postprocess or not args.include_transfers:
        warnings.append(
            "plan is not end-to-end unless preprocessing, postprocessing, and transfers are all included"
        )

    result = {
        "status": "error" if errors else "ok",
        "model_executed": False,
        "variant": "NanoTrackV3" if not args.allow_noncanonical_shapes else "caller-declared variant",
        "shapes": {
            "template_nchw": list(args.template_shape),
            "search_nchw": list(args.search_shape),
        },
        "methodology": {
            "boundary": boundary,
            "device": args.device,
            "timer": args.timer,
            "synchronize": args.synchronize,
            "warmup_calls": args.warmup,
            "timed_search_calls_per_repeat": args.iterations,
            "repeats": args.repeats,
            "num_threads": args.num_threads,
            "include_preprocess": args.include_preprocess,
            "include_postprocess": args.include_postprocess,
            "include_transfers": args.include_transfers,
        },
        "profile": {
            "macs": args.macs,
            "params": args.params,
            "tool": args.profile_tool,
            "note": "MACs are tool-native and are not relabeled as FLOPs.",
        },
        "throughput_summary": throughput_summary,
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(result, indent=args.json_indent, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
