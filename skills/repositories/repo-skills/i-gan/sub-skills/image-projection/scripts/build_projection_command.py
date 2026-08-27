#!/usr/bin/env python3
"""Build a dry-run iGAN image projection command.

This helper preserves the iGAN_predict.py CLI contract while avoiding all native
side effects: it does not import Theano, open images, touch a GPU, download
artifacts, or train models. It only renders a deterministic command/plan.
"""

from __future__ import annotations

import argparse
import json
import shlex
from typing import Dict, List

SUPPORTED_SOLVERS = ("cnn", "opt", "cnn_opt")


def derive_model_file(model_name: str, model_type: str) -> str:
    """Match iGAN_predict.py's default model-file rule."""
    return "./models/%s.%s" % (model_name, model_type)


def derive_output_image(input_image: str, solver: str) -> str:
    """Match iGAN_predict.py's literal .png replacement rule."""
    return input_image.replace(".png", "_%s.png" % solver)


def theano_flags(args: argparse.Namespace) -> str:
    """Return the THEANO_FLAGS value requested for the dry command."""
    if args.theano_flags:
        return args.theano_flags
    parts = ["device=%s" % args.device, "floatX=%s" % args.floatx]
    if args.nvcc_fastmath:
        parts.append("nvcc.fastmath=True")
    return ",".join(parts)


def build_argv(args: argparse.Namespace) -> List[str]:
    """Build the native argv without executing it."""
    argv = [
        args.python,
        args.script,
        "--model_name",
        args.model_name,
        "--model_type",
        args.model_type,
        "--input_image",
        args.input_image,
        "--solver",
        args.solver,
    ]
    if args.model_file:
        argv.extend(["--model_file", args.model_file])
    if args.output_image:
        argv.extend(["--output_image", args.output_image])
    return argv


def shell_command(args: argparse.Namespace) -> str:
    """Render a copy-pasteable shell command."""
    command = " ".join(shlex.quote(part) for part in build_argv(args))
    if args.no_theano_flags:
        return command
    return "THEANO_FLAGS=%s %s" % (shlex.quote(theano_flags(args)), command)


def plan(args: argparse.Namespace) -> Dict[str, object]:
    """Return a deterministic dry-run plan."""
    effective_model_file = args.model_file or derive_model_file(args.model_name, args.model_type)
    effective_output_image = args.output_image or derive_output_image(args.input_image, args.solver)
    warnings: List[str] = []
    if not args.output_image and ".png" not in args.input_image:
        warnings.append(
            "No --output_image was supplied and the input name does not contain '.png'; "
            "the native default may equal the input path."
        )
    if args.solver in ("cnn", "cnn_opt"):
        warnings.append(
            "This solver requires predictor params and predictor batchnorm inside the DCGAN model file."
        )
    if args.solver == "opt":
        warnings.append(
            "The original setup still compiles the predictor before dispatching opt, so missing predictor "
            "batchnorm can fail before optimization starts."
        )
    warnings.append("Default projection uses AlexNet conv4 at ./models/caffe_reference_conv4.pkl.")

    return {
        "dry_run": True,
        "native_script": args.script,
        "solver": args.solver,
        "model_name": args.model_name,
        "model_type": args.model_type,
        "model_file": effective_model_file,
        "input_image": args.input_image,
        "output_image": effective_output_image,
        "theano_flags": None if args.no_theano_flags else theano_flags(args),
        "argv": build_argv(args),
        "shell_command": shell_command(args),
        "required_artifacts": [
            effective_model_file,
            "./models/caffe_reference_conv4.pkl",
            "./lib/ilsvrc_2012_mean.npy",
            args.input_image,
        ],
        "warnings": warnings,
    }


def emit_plan(args: argparse.Namespace) -> None:
    """Print the plan in the requested deterministic format."""
    data = plan(args)
    if args.emit == "shell":
        print(data["shell_command"])
        return
    if args.emit == "json":
        print(json.dumps(data, indent=2, sort_keys=True))
        return

    print("Dry-run iGAN projection plan")
    print("command: %s" % data["shell_command"])
    print("model_file: %s" % data["model_file"])
    print("output_image: %s" % data["output_image"])
    print("required_artifacts:")
    for item in data["required_artifacts"]:
        print("  - %s" % item)
    if data["warnings"]:
        print("notes:")
        for warning in data["warnings"]:
            print("  - %s" % warning)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a dry-run command for iGAN_predict.py image projection."
    )
    parser.add_argument("--model-name", default="shoes_64", help="iGAN model name, e.g. shoes_64.")
    parser.add_argument("--model-type", default="dcgan_theano", help="iGAN model type/backend.")
    parser.add_argument("--input-image", default="./pics/shoes_test.png", help="Input image path.")
    parser.add_argument("--output-image", default=None, help="Optional reconstruction output path.")
    parser.add_argument("--model-file", default=None, help="Optional packed model path.")
    parser.add_argument("--solver", choices=SUPPORTED_SOLVERS, default="cnn_opt", help="Projection solver.")
    parser.add_argument("--python", default="python", help="Python executable token for the rendered command.")
    parser.add_argument("--script", default="iGAN_predict.py", help="Projection script path for the rendered command.")
    parser.add_argument("--device", default="gpu0", help="Theano device flag value.")
    parser.add_argument("--floatx", default="float32", help="Theano floatX flag value.")
    parser.add_argument(
        "--nvcc-fastmath",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include nvcc.fastmath=True in generated THEANO_FLAGS.",
    )
    parser.add_argument("--theano-flags", default=None, help="Override the entire THEANO_FLAGS value.")
    parser.add_argument("--no-theano-flags", action="store_true", help="Omit THEANO_FLAGS from the command.")
    parser.add_argument(
        "--emit",
        choices=("shell", "json", "plan"),
        default="shell",
        help="Output format. All formats are dry-run only.",
    )
    return parser.parse_args()


def main() -> None:
    emit_plan(parse_args())


if __name__ == "__main__":
    main()
