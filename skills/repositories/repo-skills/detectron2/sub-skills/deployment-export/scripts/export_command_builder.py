#!/usr/bin/env python3
"""Build safe Detectron2 deployment export commands without executing them."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path
from typing import Iterable, List


FORMATS_BY_METHOD = {
    "tracing": {"torchscript", "onnx"},
    "scripting": {"torchscript"},
    "caffe2_tracing": {"caffe2", "torchscript", "onnx"},
}

METHOD_NOTES = {
    "tracing": "TorchScript tracing is the safest first export path when representative sample inputs are available.",
    "scripting": "Scripting supports dynamic batch for supported official models but only writes TorchScript.",
    "caffe2_tracing": "Caffe2 tracing is optional/dependency-sensitive and should be used only when the runtime requires it.",
}


def quote_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if str(part) != "")


def split_yacs_override(text: str) -> List[str]:
    if "=" in text:
        key, value = text.split("=", 1)
        if not key or value == "":
            raise argparse.ArgumentTypeError(f"Invalid override {text!r}; expected KEY=VALUE or 'KEY VALUE'.")
        return [key, value]
    parts = text.strip().split(None, 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"Invalid override {text!r}; expected KEY=VALUE or 'KEY VALUE'.")
    return parts


def existing_path(value: str) -> str:
    if value.startswith("detectron2://") or "://" in value:
        return value
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit a Detectron2 deployment export command without running export."
    )
    parser.add_argument("--config-file", required=True, help="Config file path to pass to export_model.py.")
    parser.add_argument("--output", required=True, help="Output directory the real export command would write.")
    parser.add_argument(
        "--export-method",
        choices=sorted(FORMATS_BY_METHOD),
        default="tracing",
        help="Detectron2 export method.",
    )
    parser.add_argument(
        "--format",
        choices=sorted({fmt for formats in FORMATS_BY_METHOD.values() for fmt in formats}),
        default="torchscript",
        help="Output artifact format.",
    )
    parser.add_argument(
        "--sample-image",
        help="Representative sample image path. Strongly recommended for tracing and caffe2_tracing.",
    )
    parser.add_argument(
        "--run-eval",
        action="store_true",
        help="Include --run-eval in the printed command. This can be slow in a real run.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Yacs config override. Repeat as needed. Accepts KEY=VALUE or 'KEY VALUE'.",
    )
    parser.add_argument("--python", default="python", help="Python executable placeholder to print.")
    parser.add_argument(
        "--script",
        default="EXPORT_DRIVER.py",
        help="Export driver path to print in the command preview.",
    )
    parser.add_argument(
        "--require-sample-image",
        action="store_true",
        help="Fail if --sample-image is absent instead of printing a dataset-sample warning.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> List[str]:
    warnings: List[str] = []
    allowed_formats = FORMATS_BY_METHOD[args.export_method]
    if args.format not in allowed_formats:
        raise SystemExit(
            f"Invalid combination: --export-method {args.export_method} supports "
            f"{', '.join(sorted(allowed_formats))}, not {args.format}."
        )

    if args.export_method in {"tracing", "caffe2_tracing"} and not args.sample_image:
        message = (
            "Tracing and Caffe2 tracing need representative sample inputs. Without --sample-image, "
            "the real export script may try the first configured test-dataset batch."
        )
        if args.require_sample_image:
            raise SystemExit(message)
        warnings.append(message)

    if args.export_method == "scripting" and args.sample_image:
        warnings.append("Scripting does not need --sample-image in the standard export script; it will be included only if supplied.")

    if args.export_method == "caffe2_tracing":
        warnings.append("Caffe2 tracing requires Caffe2 support in the PyTorch build and is optional/deprecated.")

    if args.format == "onnx":
        warnings.append("ONNX export requires the onnx package and may still need custom-op/runtime work after export.")

    if args.run_eval and not (args.export_method == "tracing" and args.format == "torchscript"):
        warnings.append("The standard export script only returns an eval wrapper for some tracing/TorchScript paths; --run-eval may assert for this combination.")

    suffix = Path(args.config_file).suffix.lower()
    if suffix == ".py":
        warnings.append("The standard export_model.py command is Yacs-oriented; LazyConfig .py files may need a custom export driver.")

    if not any(split_yacs_override(item)[0] == "MODEL.WEIGHTS" for item in args.override):
        warnings.append("No MODEL.WEIGHTS override was supplied; confirm the config already points to intended weights.")

    if not any(split_yacs_override(item)[0] == "MODEL.DEVICE" for item in args.override):
        warnings.append("No MODEL.DEVICE override was supplied; confirm CPU/GPU device matches the target export environment.")

    return warnings


def build_command(args: argparse.Namespace) -> List[str]:
    command = [
        args.python,
        args.script,
        "--config-file",
        existing_path(args.config_file),
        "--output",
        args.output,
        "--export-method",
        args.export_method,
        "--format",
        args.format,
    ]
    if args.sample_image:
        command.extend(["--sample-image", existing_path(args.sample_image)])
    if args.run_eval:
        command.append("--run-eval")
    for item in args.override:
        command.extend(split_yacs_override(item))
    return command


def main() -> int:
    args = parse_args()
    warnings = validate_args(args)
    command = build_command(args)

    print("Export command preview (not executed):")
    print(quote_join(command))
    print("\nSelected export path:")
    print(f"- method: {args.export_method} - {METHOD_NOTES[args.export_method]}")
    print(f"- format: {args.format}")
    if warnings:
        print("\nReview before running:")
        for warning in warnings:
            print(f"- {warning}")
    print("\nSafety: this helper only prints a command; it does not import detectron2, load weights, build a model, or create output files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
