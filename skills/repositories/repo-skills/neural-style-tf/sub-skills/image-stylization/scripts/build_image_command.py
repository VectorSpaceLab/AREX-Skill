#!/usr/bin/env python3
"""Build a non-interactive neural_style.py single-image command.

The repository's stylize_image.sh wrapper prompts interactively, then derives
content/style directories and basenames before invoking neural_style.py. This
builder performs the path derivation and validation without prompts. It prints
an argv-safe command by default and executes only when --run is explicitly used.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


DEFAULT_MODEL_WEIGHTS = "imagenet-vgg-verydeep-19.mat"


def _quote_command(argv: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in argv)


def _expand_path(raw: str) -> Path:
    return Path(raw).expanduser()


def _display_path(path: Path) -> str:
    text = os.fspath(path)
    return text if text else "."


def _validate_file(label: str, path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"error: {label} does not exist: {_display_path(path)}")
    if not path.is_file():
        raise SystemExit(f"error: {label} is not a file: {_display_path(path)}")


def _split_for_neural_style(path: Path) -> Tuple[str, str]:
    directory = path.parent
    filename = path.name
    if not filename:
        raise SystemExit(f"error: path has no filename component: {_display_path(path)}")
    directory_text = _display_path(directory)
    return directory_text, filename


def _same_directory(paths: Iterable[Path]) -> Tuple[str, List[str]]:
    paths = list(paths)
    if not paths:
        raise SystemExit("error: at least one --style path is required")

    first_dir, _ = _split_for_neural_style(paths[0])
    filenames: List[str] = []
    for path in paths:
        style_dir, style_name = _split_for_neural_style(path)
        if os.path.normpath(style_dir) != os.path.normpath(first_dir):
            raise SystemExit(
                "error: neural_style.py accepts one --style_imgs_dir; "
                "repeatable --style paths must share one directory. "
                "Stage styles together or build a custom command with weights."
            )
        filenames.append(style_name)
    return first_dir, filenames


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate single-image content/style paths and print a safe "
            "python neural_style.py command. The command is executed only with --run."
        )
    )
    parser.add_argument(
        "--script",
        default="neural_style.py",
        help="Path to neural_style.py. Default: %(default)s",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Python executable name used in the printed command. Default: %(default)s",
    )
    parser.add_argument(
        "--content",
        required=True,
        help="Path to the content image. The builder derives --content_img_dir and --content_img.",
    )
    parser.add_argument(
        "--style",
        action="append",
        required=True,
        help=(
            "Path to a style image. Repeat for multiple style images that share one directory; "
            "the builder emits equal weights when more than one style is supplied."
        ),
    )
    parser.add_argument(
        "--output-dir",
        "--output_dir",
        dest="output_dir",
        default="./image_output",
        help="Directory passed to --img_output_dir. Default: %(default)s",
    )
    parser.add_argument(
        "--img-name",
        "--img_name",
        dest="img_name",
        default="result",
        help="Name passed to --img_name; output is nested under output-dir/img-name/. Default: %(default)s",
    )
    parser.add_argument(
        "--device",
        choices=["/cpu:0", "/gpu:0"],
        default="/cpu:0",
        help="TensorFlow device. Builder default is CPU-safe: %(default)s",
    )
    parser.add_argument(
        "--max-size",
        "--max_size",
        dest="max_size",
        type=int,
        default=None,
        help="Optional value for neural_style.py --max_size.",
    )
    parser.add_argument(
        "--max-iterations",
        "--max_iterations",
        dest="max_iterations",
        type=int,
        default=None,
        help="Optional value for neural_style.py --max_iterations.",
    )
    parser.add_argument(
        "--optimizer",
        choices=["lbfgs", "adam"],
        default=None,
        help="Optional optimizer for neural_style.py.",
    )
    parser.add_argument(
        "--model-weights",
        "--model_weights",
        dest="model_weights",
        default=None,
        help="Optional path to imagenet-vgg-verydeep-19.mat; validated when supplied.",
    )
    parser.add_argument(
        "--init-img-type",
        "--init_img_type",
        dest="init_img_type",
        choices=["content", "random", "style"],
        default=None,
        help="Optional value for neural_style.py --init_img_type.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for neural_style.py --seed; useful with --init-img-type random.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Add --verbose to the generated neural_style.py command.",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--run",
        action="store_true",
        help="Execute the generated command after printing it. Without this flag, nothing is executed.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command without executing it. This is the default behavior.",
    )
    mode.add_argument(
        "--print-only",
        action="store_true",
        help="Alias for --dry-run; print the command without executing it.",
    )

    args = parser.parse_args(argv)
    if args.max_size is not None and args.max_size <= 0:
        parser.error("--max-size must be a positive integer")
    if args.max_iterations is not None and args.max_iterations <= 0:
        parser.error("--max-iterations must be a positive integer")
    if not args.img_name or any(sep in args.img_name for sep in ("/", os.sep)):
        parser.error("--img-name must be a non-empty filename stem, not a path")
    return args


def build_command(args: argparse.Namespace) -> List[str]:
    script = _expand_path(args.script)
    content = _expand_path(args.content)
    styles = [_expand_path(style) for style in args.style]
    output_dir = _expand_path(args.output_dir)
    model_weights = _expand_path(args.model_weights) if args.model_weights else None

    _validate_file("--script", script)
    _validate_file("--content", content)
    for idx, style in enumerate(styles):
        _validate_file(f"--style[{idx}]", style)
    if model_weights is not None:
        _validate_file("--model-weights", model_weights)

    content_dir, content_name = _split_for_neural_style(content)
    style_dir, style_names = _same_directory(styles)

    command: List[str] = [
        args.python,
        _display_path(script),
        "--content_img",
        content_name,
        "--content_img_dir",
        content_dir,
        "--style_imgs",
        *style_names,
        "--style_imgs_dir",
        style_dir,
        "--img_output_dir",
        _display_path(output_dir),
        "--img_name",
        args.img_name,
        "--device",
        args.device,
    ]

    # neural_style.py defaults --style_imgs_weights to a single value. Emit one
    # equal raw weight per supplied style so every repeatable --style image is
    # represented by the source parser; custom weighting belongs to advanced use.
    if len(style_names) > 1:
        command.extend(["--style_imgs_weights", *("1.0" for _ in style_names)])

    if args.max_size is not None:
        command.extend(["--max_size", str(args.max_size)])
    if args.max_iterations is not None:
        command.extend(["--max_iterations", str(args.max_iterations)])
    if args.optimizer is not None:
        command.extend(["--optimizer", args.optimizer])
    if model_weights is not None:
        command.extend(["--model_weights", _display_path(model_weights)])
    if args.init_img_type is not None:
        command.extend(["--init_img_type", args.init_img_type])
    if args.seed is not None:
        command.extend(["--seed", str(args.seed)])
    if args.verbose:
        command.append("--verbose")

    return command


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    command = build_command(args)
    if len(args.style) > 1:
        print(
            "note: multiple --style paths are emitted with equal --style_imgs_weights; "
            "use an advanced workflow for custom style interpolation.",
            file=sys.stderr,
        )
    print(_quote_command(command))

    if not args.run:
        return 0

    if args.model_weights is None and not Path(DEFAULT_MODEL_WEIGHTS).exists():
        raise SystemExit(
            "error: --run requested but default VGG weights were not found in the current "
            f"working directory: {DEFAULT_MODEL_WEIGHTS}. Pass --model-weights explicitly."
        )

    return subprocess.call(command)


if __name__ == "__main__":
    sys.exit(main())
