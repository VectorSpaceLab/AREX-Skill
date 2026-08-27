#!/usr/bin/env python3
"""Validate MODNet configuration without importing or mutating the repo.

This is a conservative configuration check. It does not parse ONNX, inspect a
TensorRT engine, initialize CUDA, open media, download files, or execute
external commands. A zero exit status means the supplied configuration is
internally consistent, not that the backend or artifacts are runnable.
"""

import argparse
from pathlib import Path
import sys


BACKGROUND_SUFFIXES = {".jpg", ".png", ".mp4", ".ts"}
SOURCE_SUFFIXES = {".jpg", ".jpeg", ".png", ".mp4", ".ts", ".avi", ".mkv"}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Safely check fixed-shape MODNet export/build/demo settings; "
            "does not import CUDA/TensorRT or mutate files."
        )
    )
    p.add_argument("--export-width", type=int, default=512)
    p.add_argument("--export-height", type=int, default=288)
    p.add_argument("--builder-width", type=int)
    p.add_argument("--builder-height", type=int)
    p.add_argument("--onnx", type=Path, help="ONNX path (existence is checked)")
    p.add_argument("--engine", type=Path, help="engine path (existence is checked)")
    p.add_argument("--checkpoint", type=Path, help="checkpoint path (existence is checked)")
    p.add_argument("--require-artifacts", action="store_true",
                   help="make supplied artifact paths and their files mandatory")
    p.add_argument("--profile-input-name", default="input",
                   help="name used by the TensorRT optimization profile")
    p.add_argument("--onnx-input-name", default="input",
                   help="expected ONNX input name from the exporter")
    p.add_argument("--tensorrt-major", type=int,
                   help="known TensorRT major version, for compatibility warnings")
    p.add_argument("--tensorrt-minor", type=int, default=0,
                   help="known TensorRT minor version (used with --tensorrt-major)")
    p.add_argument("--input", type=Path,
                   help="optional foreground image/video path to check")
    p.add_argument("--background", type=Path,
                   help="optional background path; use no argument for black")
    p.add_argument("--create-video", metavar="BASENAME",
                   help="optional output basename; repository appends .ts/.mp4")
    return p


def check_file(path: Path, label: str, errors: list[str], warnings: list[str], required: bool) -> None:
    if path.exists() and path.is_file():
        print(f"OK   {label}: {path}")
        return
    message = f"missing or non-regular {label}: {path}"
    (errors if required else warnings).append(message)
    print(("ERROR" if required else "WARN ") + " " + message)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []

    if args.export_width <= 0 or args.export_height <= 0:
        errors.append("export dimensions must be positive")
    if args.export_width % 4 or args.export_height % 4:
        errors.append("export width and height must both be divisible by 4")

    builder_width = args.builder_width if args.builder_width is not None else args.export_width
    builder_height = args.builder_height if args.builder_height is not None else args.export_height
    if builder_width != args.export_width or builder_height != args.export_height:
        errors.append(
            "TensorRT builder dimensions must equal fixed ONNX export dimensions "
            f"({args.export_width}x{args.export_height}); got {builder_width}x{builder_height}"
        )

    if args.onnx_input_name != "input":
        warnings.append(
            f"exporter normally writes input name 'input', not {args.onnx_input_name!r}"
        )
    if args.profile_input_name != args.onnx_input_name:
        errors.append(
            "TensorRT profile input name must equal the ONNX input name "
            f"({args.onnx_input_name!r}); got {args.profile_input_name!r}"
        )

    if args.tensorrt_major is not None:
        if args.tensorrt_major < 7:
            errors.append("MODNet TensorRT path requires TensorRT major version 7 or newer")
        elif args.tensorrt_major == 7 and args.tensorrt_minor == 1:
            warnings.append(
                "TensorRT 7.1 needs the documented onnx-tensorrt InstanceNormalization workaround"
            )
        elif args.tensorrt_major == 7 and args.tensorrt_minor >= 2:
            print("OK   TensorRT 7.2+ standard MODNet builder path selected")

    for path, label in (
        (args.checkpoint, "checkpoint"),
        (args.onnx, "ONNX graph"),
        (args.engine, "TensorRT engine"),
    ):
        if path is not None:
            check_file(path, label, errors, warnings, args.require_artifacts)

    if args.input is not None:
        suffix = args.input.suffix.lower()
        if suffix not in SOURCE_SUFFIXES:
            errors.append(
                f"unsupported foreground suffix {args.input.suffix!r}; "
                "the stock Camera supports common image/video files, but this suffix is not recognized"
            )
        check_file(args.input, "foreground input", errors, warnings, args.require_artifacts)

    if args.background is not None:
        suffix = args.background.suffix.lower()
        if suffix not in BACKGROUND_SUFFIXES:
            errors.append(
                f"unsupported background suffix {args.background.suffix!r}; "
                "use lowercase .jpg, .png, .mp4, or .ts"
            )
        check_file(args.background, "background", errors, warnings, args.require_artifacts)
    else:
        print("OK   background: empty argument means black background")

    if args.create_video:
        output = Path(args.create_video)
        if output.suffix.lower() in {".ts", ".mp4"}:
            warnings.append(
                "--create_video is a basename; the repository appends .ts or .mp4, "
                f"so passing {output.name!r} may produce a doubled extension"
            )
        if output.name in {"", ".", ".."}:
            errors.append("--create_video must name an output basename")

    print(f"CONFIG export tensor: [1, 3, {args.export_height}, {args.export_width}]")
    print(f"CONFIG TensorRT profile: [1, 3, {builder_height}, {builder_width}]")
    for warning in warnings:
        if not warning.startswith("missing or non-regular"):
            print("WARN " + warning)

    if errors:
        for error in errors:
            print("ERROR " + error, file=sys.stderr)
        print(f"FAIL {len(errors)} configuration error(s)", file=sys.stderr)
        return 2
    if warnings:
        print(f"PASS with {len(warnings)} warning(s)")
    else:
        print("PASS configuration checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
