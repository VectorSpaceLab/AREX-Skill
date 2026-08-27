#!/usr/bin/env python3
"""Build a dry-run iGAN headless constraint-generation command.

This helper adapts the native iGAN_script.py command-line contract into a safe
planner. It prints the command that a caller may run in a prepared legacy iGAN
checkout, but it never imports iGAN, Theano, OpenCV, PyQt4, or CUDA libraries
and never executes the command.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shlex
import sys
from typing import Dict, List, Optional


DEFAULT_THEANO_FLAGS = "device=gpu0,floatX=float32,nvcc.fastmath=True"


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def nonnegative_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a float, got {value!r}") from exc
    if parsed < 0.0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def quote_argv(argv: List[str]) -> str:
    return " ".join(shlex.quote(part) for part in argv)


def build_argv(args: argparse.Namespace) -> List[str]:
    script_path = args.script
    if args.repo_root:
        script_path = os.path.join(args.repo_root, args.script)

    argv = [
        args.python,
        script_path,
        "--model_name",
        args.model_name,
        "--model_type",
        args.model_type,
        "--framework",
        args.framework,
        "--input_color",
        args.input_color,
        "--input_color_mask",
        args.input_color_mask,
        "--input_edge",
        args.input_edge,
        "--output_result",
        args.output_result,
        "--batch_size",
        str(args.batch_size),
        "--n_iters",
        str(args.n_iters),
        "--top_k",
        str(args.top_k),
        "--d_weight",
        str(args.d_weight),
    ]
    if args.model_file:
        argv.extend(["--model_file", args.model_file])
    return argv


def layout_plan(args: argparse.Namespace) -> Dict[str, object]:
    panels_before_resize = 3 + args.top_k
    pre_width = args.target_size * panels_before_resize
    pre_height = args.target_size
    final_width = int(round(pre_width * args.native_resize_scale))
    final_height = int(round(pre_height * args.native_resize_scale))
    grid_warning: Optional[str] = None
    if args.top_k > args.batch_size:
        grid_warning = (
            "top_k is greater than batch_size; the native optimizer cannot "
            "select more candidate images than the number of latent initializations."
        )
    return {
        "target_size": args.target_size,
        "input_panels": 3,
        "max_candidate_panels": args.top_k,
        "max_total_panels": panels_before_resize,
        "pre_resize_width": pre_width,
        "pre_resize_height": pre_height,
        "native_resize_scale": args.native_resize_scale,
        "final_width": final_width,
        "final_height": final_height,
        "candidate_layout": "horizontal-strip",
        "warning": grid_warning,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a dry-run command for iGAN_script.py constrained generation "
            "and estimate the output visualization layout."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Directory containing iGAN_script.py for the eventual native run (default: current directory).",
    )
    parser.add_argument(
        "--script",
        default="iGAN_script.py",
        help="Headless script path relative to --repo-root (default: iGAN_script.py).",
    )
    parser.add_argument("--python", default="python", help="Python executable for the eventual native run.")
    parser.add_argument("--model-name", default="outdoor_64", help="iGAN model configuration name.")
    parser.add_argument("--model-type", default="dcgan_theano", help="Generative model implementation name.")
    parser.add_argument("--framework", default="theano", help="Constrained optimizer backend name.")
    parser.add_argument("--model-file", default=None, help="Optional explicit model artifact path.")
    parser.add_argument("--input-color", default="./pics/input_color.png", help="Color constraint image path.")
    parser.add_argument("--input-color-mask", default="./pics/input_color_mask.png", help="Color mask image path.")
    parser.add_argument("--input-edge", default="./pics/input_edge.png", help="Edge/sketch constraint image path.")
    parser.add_argument("--output-result", default="./pics/script_result.png", help="Output visualization image path.")
    parser.add_argument("--batch-size", type=positive_int, default=64, help="Number of latent initializations.")
    parser.add_argument("--n-iters", type=positive_int, default=100, help="Number of optimization iterations.")
    parser.add_argument("--top-k", type=positive_int, default=16, help="Maximum number of candidate panels.")
    parser.add_argument("--d-weight", type=nonnegative_float, default=0.0, help="Discriminator realism weight.")
    parser.add_argument("--target-size", type=positive_int, default=64, help="Model image size used for layout planning.")
    parser.add_argument(
        "--native-resize-scale",
        type=nonnegative_float,
        default=2.0,
        help="Final resize scale used by the native script for the visualization.",
    )
    parser.add_argument(
        "--theano-flags",
        default=DEFAULT_THEANO_FLAGS,
        help="THEANO_FLAGS value to prepend in shell output.",
    )
    parser.add_argument(
        "--no-theano-flags",
        action="store_true",
        help="Do not prepend THEANO_FLAGS in shell output.",
    )
    parser.add_argument(
        "--format",
        choices=("shell", "json"),
        default="shell",
        help="Output format (default: shell).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Accepted for clarity; this helper is always dry-run and never executes the command.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.native_resize_scale <= 0.0:
        parser.error("--native-resize-scale must be positive")

    command_argv = build_argv(args)
    shell_command = quote_argv(command_argv)
    env: Dict[str, str] = {}
    if not args.no_theano_flags and args.theano_flags:
        env["THEANO_FLAGS"] = args.theano_flags
        shell_command = f"THEANO_FLAGS={shlex.quote(args.theano_flags)} {shell_command}"

    plan = layout_plan(args)
    payload = {
        "dry_run": True,
        "cwd": args.repo_root,
        "env": env,
        "argv": command_argv,
        "shell_command": shell_command,
        "layout_plan": plan,
        "notes": [
            "Command is not executed by this helper.",
            "Run native command only after model artifacts and legacy Theano/OpenCV/PyQt4 runtime are verified.",
        ],
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("# Dry-run iGAN constraint-generation command")
        print(shell_command)
        print("\n# Output layout estimate")
        print(
            "# target_size={target_size}, input_panels={input_panels}, "
            "max_candidate_panels={max_candidate_panels}, final_size={final_width}x{final_height}, "
            "layout={candidate_layout}".format(**plan)
        )
        if plan["warning"]:
            print(f"# WARNING: {plan['warning']}")
        print("# This helper did not run iGAN or touch the GPU.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
