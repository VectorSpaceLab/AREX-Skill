#!/usr/bin/env python3
"""Build dry timm ONNX export and validation commands."""

import argparse
import shlex
from pathlib import Path
from typing import Iterable, List, Optional


def _append_option(command: List[str], flag: str, value: Optional[object]) -> None:
    if value is not None and value != "":
        command.extend([flag, str(value)])


def _append_multi(command: List[str], flag: str, values: Optional[Iterable[object]]) -> None:
    if values:
        command.append(flag)
        command.extend(str(value) for value in values)


def _quote(command: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def build_export_command(args: argparse.Namespace) -> List[str]:
    command = [args.python, args.script, args.output]
    _append_option(command, "--model", args.model)
    _append_option(command, "--opset", args.opset)
    _append_option(command, "--batch-size", args.batch_size)
    _append_option(command, "--img-size", args.img_size)
    _append_multi(command, "--input-size", args.input_size)
    _append_multi(command, "--mean", args.mean)
    _append_multi(command, "--std", args.std)
    _append_option(command, "--num-classes", args.num_classes)
    _append_option(command, "--checkpoint", args.checkpoint)

    for enabled, flag in (
        (args.keep_init, "--keep-init"),
        (args.aten_fallback, "--aten-fallback"),
        (args.dynamic_size, "--dynamic-size"),
        (args.check_forward, "--check-forward"),
        (args.reparam, "--reparam"),
        (args.training, "--training"),
        (args.verbose, "--verbose"),
        (args.dynamo, "--dynamo"),
    ):
        if enabled:
            command.append(flag)
    return command


def build_validate_command(args: argparse.Namespace) -> List[str]:
    command = [args.python, args.script, args.data]
    _append_option(command, "--onnx-input", args.onnx_input)
    _append_option(command, "--onnx-output-opt", args.onnx_output_opt)
    _append_option(command, "--workers", args.workers)
    _append_option(command, "--batch-size", args.batch_size)
    _append_option(command, "--img-size", args.img_size)
    _append_multi(command, "--mean", args.mean)
    _append_multi(command, "--std", args.std)
    _append_option(command, "--crop-pct", args.crop_pct)
    _append_option(command, "--interpolation", args.interpolation)
    _append_option(command, "--print-freq", args.print_freq)
    if args.profile:
        command.append("--profile")
    return command


def add_common_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--python", default="python", help="Python executable token to print in the command.")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    export = subparsers.add_parser("export", help="Print an onnx_export.py command.")
    add_common_parser(export)
    export.add_argument("--script", default="onnx_export.py", help="Path to the timm ONNX export script.")
    export.add_argument("--output", required=True, help="Output ONNX filename.")
    export.add_argument("--model", default="mobilenetv3_large_100", help="timm model name.")
    export.add_argument("--opset", type=int, default=None, help="ONNX opset.")
    export.add_argument("--keep-init", action="store_true", help="Keep initializers as inputs.")
    export.add_argument("--aten-fallback", action="store_true", help="Allow ATEN fallback ops.")
    export.add_argument("--dynamic-size", action="store_true", help="Export dynamic width/height axes.")
    export.add_argument("--check-forward", action="store_true", help="Add export-time PyTorch/ONNX forward check.")
    export.add_argument("--batch-size", type=int, default=1, help="Export batch size.")
    export.add_argument("--img-size", type=int, default=None, help="Square image size shortcut.")
    export.add_argument("--input-size", nargs=3, type=int, default=None, metavar=("C", "H", "W"), help="Input size.")
    export.add_argument("--mean", nargs="+", type=float, default=None, help="Dataset mean override.")
    export.add_argument("--std", nargs="+", type=float, default=None, help="Dataset std override.")
    export.add_argument("--num-classes", type=int, default=None, help="Number of classes.")
    export.add_argument("--checkpoint", default="", help="Local checkpoint path.")
    export.add_argument("--reparam", action="store_true", help="Reparameterize model before export.")
    export.add_argument("--training", action="store_true", help="Export in training mode.")
    export.add_argument("--verbose", action="store_true", help="Enable verbose export output.")
    export.add_argument("--dynamo", action="store_true", help="Use Torch Dynamo export path.")
    export.set_defaults(builder=build_export_command)

    validate = subparsers.add_parser("validate", help="Print an onnx_validate.py command.")
    add_common_parser(validate)
    validate.add_argument("--script", default="onnx_validate.py", help="Path to the timm ONNX validation script.")
    validate.add_argument("--data", required=True, help="Validation dataset directory.")
    validate.add_argument("--onnx-input", required=True, help="Path to ONNX model file.")
    validate.add_argument("--onnx-output-opt", default="", help="Optional optimized graph output path.")
    validate.add_argument("--profile", action="store_true", help="Enable ONNX Runtime profiling.")
    validate.add_argument("--workers", type=int, default=2, help="Data loading workers.")
    validate.add_argument("--batch-size", type=int, default=256, help="Validation batch size.")
    validate.add_argument("--img-size", type=int, default=None, help="Input image dimension.")
    validate.add_argument("--mean", nargs="+", type=float, default=None, help="Dataset mean override.")
    validate.add_argument("--std", nargs="+", type=float, default=None, help="Dataset std override.")
    validate.add_argument("--crop-pct", type=float, default=None, help="Crop percentage override.")
    validate.add_argument("--interpolation", default="", help="Resize interpolation override.")
    validate.add_argument("--print-freq", type=int, default=10, help="Print frequency.")
    validate.set_defaults(builder=build_validate_command)
    return parser


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()
    command = args.builder(args)
    print(_quote(command))


if __name__ == "__main__":
    main()
