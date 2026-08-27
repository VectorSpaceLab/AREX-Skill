#!/usr/bin/env python3
"""Generate safe D-FINE inference commands without executing them."""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}


def _q(value: object) -> str:
    return shlex.quote(str(value))


def _media_kind(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    return "unknown"


def _expected_output(backend: str, input_path: str) -> str:
    kind = _media_kind(input_path)
    if backend == "openvino":
        return "openvino_result.jpg"
    if backend == "torch":
        return "torch_results.jpg" if kind != "video" else "torch_results.mp4"
    if backend == "onnx":
        return "onnx_result.jpg" if kind != "video" else "onnx_result.mp4"
    if backend == "trt":
        return "trt_result.jpg" if kind != "video" else "trt_result.mp4"
    raise ValueError(f"Unsupported backend: {backend}")


def build_command(args: argparse.Namespace) -> tuple[str, str]:
    backend = args.backend
    if backend == "torch":
        if not args.config or not args.checkpoint:
            raise SystemExit("torch backend requires --config and --checkpoint")
        command = [
            args.python,
            "tools/inference/torch_inf.py",
            "-c",
            args.config,
            "-r",
            args.checkpoint,
            "--input",
            args.input,
            "--device",
            args.device,
        ]
        if args.extra:
            command.extend(args.extra)
        return " ".join(_q(part) for part in command), _expected_output(backend, args.input)

    if backend == "onnx":
        if not args.onnx_model:
            raise SystemExit("onnx backend requires --onnx-model")
        command = [args.python, "tools/inference/onnx_inf.py", "--onnx", args.onnx_model, "--input", args.input]
        if args.extra:
            command.extend(args.extra)
        return " ".join(_q(part) for part in command), _expected_output(backend, args.input)

    if backend == "openvino":
        if not args.openvino_model:
            raise SystemExit("openvino backend requires --openvino-model")
        if _media_kind(args.input) == "video":
            raise SystemExit("openvino backend is image-only in the native CLI; use an image input")
        command = [
            args.python,
            "tools/inference/openvino_inf.py",
            "--ov_model",
            args.openvino_model,
            "--image",
            args.input,
        ]
        if args.extra:
            command.extend(args.extra)
        return " ".join(_q(part) for part in command), _expected_output(backend, args.input)

    if backend == "trt":
        if not args.trt_engine:
            raise SystemExit("trt backend requires --trt-engine")
        command = [
            args.python,
            "tools/inference/trt_inf.py",
            "--trt",
            args.trt_engine,
            "--input",
            args.input,
            "--device",
            args.device,
        ]
        if args.extra:
            command.extend(args.extra)
        return " ".join(_q(part) for part in command), _expected_output(backend, args.input)

    raise SystemExit(f"Unsupported backend: {backend}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate safe D-FINE inference commands for torch, onnx, openvino, or trt."
    )
    parser.add_argument("--backend", choices=["torch", "onnx", "openvino", "trt"], required=True)
    parser.add_argument("--input", required=True, help="Image or video path for the native inference script.")
    parser.add_argument("--config", help="D-FINE YAML config for torch inference.")
    parser.add_argument("--checkpoint", help="Checkpoint path for torch inference.")
    parser.add_argument("--onnx-model", help="ONNX model path for ONNX Runtime inference.")
    parser.add_argument("--openvino-model", help="OpenVINO IR/XML model path for OpenVINO inference.")
    parser.add_argument("--trt-engine", help="TensorRT engine path for TensorRT inference.")
    parser.add_argument("--device", default="cpu", help="Device string used by the native CLI when supported.")
    parser.add_argument("--python", default="python", help="Python command to place at the front of the recipe.")
    parser.add_argument(
        "--extra",
        nargs=argparse.REMAINDER,
        default=[],
        help="Additional literal arguments appended to the generated command.",
    )
    parser.add_argument(
        "--check-paths",
        action="store_true",
        help="Verify that provided paths exist before printing the command.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.check_paths:
        path_fields = [
            ("--input", args.input),
            ("--config", args.config),
            ("--checkpoint", args.checkpoint),
            ("--onnx-model", args.onnx_model),
            ("--openvino-model", args.openvino_model),
            ("--trt-engine", args.trt_engine),
        ]
        missing = [flag for flag, path in path_fields if path and not Path(path).exists()]
        if missing:
            raise SystemExit(f"Missing path(s) for {', '.join(missing)}")

    command, output_file = build_command(args)

    notes: list[str] = []
    if args.backend == "openvino":
        notes.append("native CLI is image-only and uses AUTO device selection")
    if args.backend == "torch":
        notes.append("native preprocessing resizes directly to 640x640")
    if args.backend == "onnx":
        notes.append("native preprocessing keeps aspect ratio and pads to a square canvas")
    if args.backend == "trt":
        notes.append("native preprocessing resizes directly to 640x640")

    print(f"backend: {args.backend}")
    print(f"expected output: {output_file}")
    if notes:
        print(f"notes: {'; '.join(notes)}")
    print("command:")
    print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
