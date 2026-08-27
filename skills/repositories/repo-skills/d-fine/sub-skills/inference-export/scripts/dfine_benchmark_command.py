#!/usr/bin/env python3
"""Generate safe D-FINE benchmark commands without executing them."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def _q(value: object) -> str:
    return shlex.quote(str(value))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate safe D-FINE FLOPs or TensorRT benchmark commands."
    )
    parser.add_argument("--benchmark", choices=["flops", "trt"], required=True)
    parser.add_argument(
        "--config",
        default="configs/dfine/dfine_hgnetv2_l_coco.yml",
        help="D-FINE YAML config used for FLOPs/params benchmarking.",
    )
    parser.add_argument(
        "--infer-dir",
        help="Directory containing .jpg images for TensorRT latency benchmarking.",
    )
    parser.add_argument(
        "--engine-dir",
        help="Directory containing one or more TensorRT .engine files.",
    )
    parser.add_argument("--busy", action="store_true", help="Include the native busy flag.")
    parser.add_argument("--python", default="python", help="Python command to place at the front.")
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Verify that provided paths exist before printing the command.",
    )
    return parser.parse_args(argv)


def _flops_command(args: argparse.Namespace) -> str:
    return " ".join(
        _q(part)
        for part in [args.python, "tools/benchmark/get_info.py", "-c", args.config]
    )


def _trt_command(args: argparse.Namespace) -> str:
    if not args.infer_dir or not args.engine_dir:
        raise SystemExit("trt benchmark requires --infer-dir and --engine-dir")
    parts = [
        args.python,
        "tools/benchmark/trt_benchmark.py",
        "--infer_dir",
        args.infer_dir,
        "--engine_dir",
        args.engine_dir,
    ]
    if args.busy:
        parts.append("--busy")
    return " ".join(_q(part) for part in parts)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.check_paths:
        missing = []
        if args.config and not Path(args.config).exists():
            missing.append("--config")
        if args.infer_dir and not Path(args.infer_dir).exists():
            missing.append("--infer-dir")
        if args.engine_dir and not Path(args.engine_dir).exists():
            missing.append("--engine-dir")
        if missing:
            raise SystemExit(f"Missing path(s) for {', '.join(missing)}")

    if args.benchmark == "flops":
        print("benchmark: flops")
        print("expected output: stdout only")
        print("command:")
        print(_flops_command(args))
        return 0

    if args.benchmark == "trt":
        print("benchmark: trt")
        print("expected output: stdout latency summary")
        print("command:")
        print(_trt_command(args))
        return 0

    raise SystemExit(f"Unsupported benchmark: {args.benchmark}")


if __name__ == "__main__":
    raise SystemExit(main())
