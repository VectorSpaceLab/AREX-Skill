#!/usr/bin/env python3
"""Generate safe D-FINE ONNX export and optional TensorRT build commands."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def _q(value: object) -> str:
    return shlex.quote(str(value))


def _native_onnx_name(checkpoint: str, requested: str | None) -> str:
    if requested:
        return requested
    if checkpoint.endswith(".pth"):
        return str(Path(checkpoint).with_suffix(".onnx"))
    return "model.onnx"


def _engine_name(onnx_name: str, requested: str | None) -> str:
    if requested:
        return requested
    return str(Path(onnx_name).with_suffix(".engine"))


def _export_command(args: argparse.Namespace, onnx_name: str) -> str:
    return " ".join(
        _q(part)
        for part in [
            args.python,
            "tools/deployment/export_onnx.py",
            "--check",
            "--simplify",
            "-c",
            args.config,
            "-r",
            args.checkpoint,
        ]
    )


def _trtexec_command(args: argparse.Namespace, onnx_name: str, engine_name: str) -> str:
    size = args.image_size
    min_shapes = f"images:1x3x{size}x{size},orig_target_sizes:1x2"
    opt_shapes = f"images:1x3x{size}x{size},orig_target_sizes:1x2"
    max_shapes = f"images:{args.max_batch}x3x{size}x{size},orig_target_sizes:{args.max_batch}x2"
    parts = [
        args.trtexec,
        f"--onnx={onnx_name}",
        f"--saveEngine={engine_name}",
        f"--minShapes={min_shapes}",
        f"--optShapes={opt_shapes}",
        f"--maxShapes={max_shapes}",
    ]
    if args.fp16:
        parts.append("--fp16")
    if args.extra_trt:
        parts.extend(args.extra_trt)
    return " ".join(_q(part) for part in parts)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate safe D-FINE ONNX export and optional TensorRT build commands."
    )
    parser.add_argument("--config", required=True, help="D-FINE YAML config used for export.")
    parser.add_argument("--checkpoint", required=True, help="Trained checkpoint to export.")
    parser.add_argument(
        "--onnx-output",
        help="Desired ONNX filename in the printed recipe. Defaults to the exporter-derived name.",
    )
    parser.add_argument(
        "--build-trt",
        action="store_true",
        help="Also print a TensorRT build command that consumes the ONNX output.",
    )
    parser.add_argument(
        "--trt-engine",
        help="Desired TensorRT engine filename. Defaults to the ONNX stem with .engine.",
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=640,
        help="Square image size used for the trtexec shape profile.",
    )
    parser.add_argument(
        "--max-batch",
        type=int,
        default=32,
        help="Maximum batch size used for the trtexec shape profile.",
    )
    parser.add_argument(
        "--fp16",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include --fp16 in the printed TensorRT build command.",
    )
    parser.add_argument("--python", default="python", help="Python command to place at the front.")
    parser.add_argument("--trtexec", default="trtexec", help="TensorRT command-line binary.")
    parser.add_argument(
        "--extra-trt",
        nargs=argparse.REMAINDER,
        default=[],
        help="Additional literal arguments appended to the printed trtexec command.",
    )
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Verify that the config and checkpoint exist before printing commands.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.check_paths:
        missing = [
            flag
            for flag, path in [("--config", args.config), ("--checkpoint", args.checkpoint)]
            if path and not Path(path).exists()
        ]
        if missing:
            raise SystemExit(f"Missing path(s) for {', '.join(missing)}")

    onnx_name = _native_onnx_name(args.checkpoint, args.onnx_output)
    engine_name = _engine_name(onnx_name, args.trt_engine)
    export_command = _export_command(args, onnx_name)

    print("export recipe:")
    print(f"  expected onnx: {onnx_name}")
    print(f"  command: {export_command}")

    native_output = str(Path(args.checkpoint).with_suffix(".onnx")) if args.checkpoint.endswith(".pth") else "model.onnx"
    if onnx_name != native_output:
        print(f"  note: the native exporter will first write {native_output}; rename it if you want {onnx_name}")

    if args.build_trt:
        trt_command = _trtexec_command(args, onnx_name, engine_name)
        print("trt recipe:")
        print(f"  expected engine: {engine_name}")
        print(f"  command: {trt_command}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
