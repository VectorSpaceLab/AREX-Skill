#!/usr/bin/env python3
"""Validate and print advanced neural_style.py flag fragments.

This helper does not import TensorFlow or run stylization. It catches common
count mismatches that neural_style.py may otherwise accept and then ignore via
zip(...), normalizes weight ratios the way the source parser does, and prints a
shell-safe fragment to append to a base command.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from typing import Iterable, List, Optional, Sequence


DEFAULT_STYLE_LAYERS = ["relu1_1", "relu2_1", "relu3_1", "relu4_1", "relu5_1"]
DEFAULT_CONTENT_LAYERS = ["conv4_2"]


def normalize(values: Sequence[float]) -> List[float]:
    total = sum(values)
    if total <= 0:
        raise ValueError("weight sum must be positive")
    return [float(v) / total for v in values]


def shell_join(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def positive_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a float: {text}")
    if value < 0:
        raise argparse.ArgumentTypeError("weights must be non-negative")
    return value


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate count-sensitive advanced neural_style.py flags and print a safe flag fragment."
    )
    parser.add_argument("--style", action="append", default=[], help="Style image filename or path. Repeat once per style image.")
    parser.add_argument("--style-weight", action="append", type=positive_float, default=None, help="Raw style image weight. Repeat once per --style.")
    parser.add_argument("--style-mask", action="store_true", help="Emit --style_mask and validate --style-mask-img count.")
    parser.add_argument("--style-mask-img", action="append", default=None, help="Mask filename read from content image directory. Repeat once per style image.")
    parser.add_argument("--original-colors", action="store_true", help="Emit --original_colors.")
    parser.add_argument("--color-convert-type", choices=["yuv", "ycrcb", "luv", "lab"], default=None, help="Color conversion type for --original_colors.")
    parser.add_argument("--color-convert-time", choices=["after", "before"], default=None, help="Parsed by source, but inspected implementation always converts after stylization.")
    parser.add_argument("--content-layer", action="append", default=None, help="Content layer. Repeat for multiple layers.")
    parser.add_argument("--content-layer-weight", action="append", type=positive_float, default=None, help="Raw content-layer weight. Repeat once per content layer.")
    parser.add_argument("--style-layer", action="append", default=None, help="Style layer. Repeat for multiple layers.")
    parser.add_argument("--style-layer-weight", action="append", type=positive_float, default=None, help="Raw style-layer weight. Repeat once per style layer.")
    parser.add_argument("--content-loss-function", type=int, choices=[1, 2, 3], default=None)
    parser.add_argument("--content-weight", type=float, default=None)
    parser.add_argument("--style-weight-total", type=float, default=None, help="Value for neural_style.py --style_weight, not per-style interpolation.")
    parser.add_argument("--tv-weight", type=float, default=None)
    parser.add_argument("--optimizer", choices=["lbfgs", "adam"], default=None)
    parser.add_argument("--learning-rate", type=float, default=None)
    parser.add_argument("--init-img-type", choices=["content", "random", "style"], default=None)
    parser.add_argument("--noise-ratio", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--pooling-type", choices=["avg", "max"], default=None)
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of shell fragment only.")
    args = parser.parse_args(argv)

    if args.style_weight is not None and not args.style:
        parser.error("--style-weight requires at least one --style")
    if args.style_weight is not None and len(args.style_weight) != len(args.style):
        parser.error("--style-weight count must match --style count")
    if args.style_mask_img is not None and not args.style_mask:
        parser.error("--style-mask-img requires --style-mask")
    if args.style_mask and not args.style_mask_img:
        parser.error("--style-mask requires one --style-mask-img per style image")
    if args.style_mask and args.style and len(args.style_mask_img or []) != len(args.style):
        parser.error("--style-mask-img count must match --style count")

    content_layers = args.content_layer or []
    style_layers = args.style_layer or []
    if args.content_layer_weight is not None:
        expected = len(content_layers) if content_layers else len(DEFAULT_CONTENT_LAYERS)
        if len(args.content_layer_weight) != expected:
            parser.error("--content-layer-weight count must match content layer count")
    if args.style_layer_weight is not None:
        expected = len(style_layers) if style_layers else len(DEFAULT_STYLE_LAYERS)
        if len(args.style_layer_weight) != expected:
            parser.error("--style-layer-weight count must match style layer count")
    if args.noise_ratio is not None and not (0.0 <= args.noise_ratio <= 1.0):
        parser.error("--noise-ratio should be between 0 and 1")
    if args.learning_rate is not None and args.learning_rate <= 0:
        parser.error("--learning-rate must be positive")
    return args


def build_fragment(args: argparse.Namespace) -> List[str]:
    fragment: List[str] = []
    normalized = {}

    if args.style:
        fragment.extend(["--style_imgs", *args.style])
    if args.style_weight is not None:
        norm = normalize(args.style_weight)
        normalized["style_imgs_weights"] = norm
        fragment.extend(["--style_imgs_weights", *[str(v) for v in args.style_weight]])

    if args.style_mask:
        fragment.append("--style_mask")
        fragment.extend(["--style_mask_imgs", *(args.style_mask_img or [])])

    if args.original_colors:
        fragment.append("--original_colors")
    if args.color_convert_type:
        fragment.extend(["--color_convert_type", args.color_convert_type])
    if args.color_convert_time:
        fragment.extend(["--color_convert_time", args.color_convert_time])

    if args.content_layer:
        fragment.extend(["--content_layers", *args.content_layer])
    if args.content_layer_weight is not None:
        normalized["content_layer_weights"] = normalize(args.content_layer_weight)
        fragment.extend(["--content_layer_weights", *[str(v) for v in args.content_layer_weight]])
    if args.style_layer:
        fragment.extend(["--style_layers", *args.style_layer])
    if args.style_layer_weight is not None:
        normalized["style_layer_weights"] = normalize(args.style_layer_weight)
        fragment.extend(["--style_layer_weights", *[str(v) for v in args.style_layer_weight]])

    scalar_map = [
        ("content_loss_function", args.content_loss_function),
        ("content_weight", args.content_weight),
        ("style_weight", args.style_weight_total),
        ("tv_weight", args.tv_weight),
        ("optimizer", args.optimizer),
        ("learning_rate", args.learning_rate),
        ("init_img_type", args.init_img_type),
        ("noise_ratio", args.noise_ratio),
        ("seed", args.seed),
        ("pooling_type", args.pooling_type),
    ]
    for name, value in scalar_map:
        if value is not None:
            fragment.extend(["--" + name, str(value)])

    return fragment, normalized


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        fragment, normalized = build_fragment(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.color_convert_time == "before":
        print(
            "warning: inspected source parses --color_convert_time before, but conversion is implemented after stylization.",
            file=sys.stderr,
        )
    if args.style_mask:
        print("note: mask filenames are read from --content_img_dir in neural_style.py.", file=sys.stderr)

    if args.json:
        print(json.dumps({"fragment": fragment, "normalizedWeights": normalized}, indent=2, sort_keys=True))
    else:
        print(shell_join(fragment))
        if normalized:
            print("# normalized weights: " + json.dumps(normalized, sort_keys=True), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
