#!/usr/bin/env python3
"""Build ECCV2022-RIFE interpolation commands without running inference.

The helper is intentionally safe: it prints a command for the repository's
source scripts and optionally validates paths/checkpoint layout. It never runs
long image or video inference.
"""
from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

VALID_SCALES = {0.25, 0.5, 1.0, 2.0, 4.0}


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def resolve_for_validation(path_text: Optional[str], repo_root: Optional[Path]) -> Optional[Path]:
    if path_text is None:
        return None
    path = Path(path_text).expanduser()
    if not path.is_absolute() and repo_root is not None:
        path = repo_root / path
    return path


def existing_path(path_text: str, repo_root: Optional[Path]) -> Path:
    path = resolve_for_validation(path_text, repo_root)
    assert path is not None
    return path


def add_error(errors: List[str], message: str) -> None:
    errors.append(f"ERROR: {message}")


def add_warning(warnings: List[str], message: str) -> None:
    warnings.append(f"WARNING: {message}")


def check_file(label: str, path_text: str, repo_root: Optional[Path], errors: List[str]) -> None:
    path = existing_path(path_text, repo_root)
    if not path.is_file():
        add_error(errors, f"{label} is not a readable file: {path_text}")


def check_dir(label: str, path_text: str, repo_root: Optional[Path], errors: List[str]) -> Optional[Path]:
    path = existing_path(path_text, repo_root)
    if not path.is_dir():
        add_error(errors, f"{label} is not a directory: {path_text}")
        return None
    return path


def validate_model_dir(model_text: str, repo_root: Optional[Path], errors: List[str], warnings: List[str]) -> None:
    model_dir = check_dir("model directory", model_text, repo_root, errors)
    if model_dir is None:
        return
    pkl_files = sorted(p.name for p in model_dir.glob("*.pkl"))
    if not pkl_files:
        add_error(errors, f"model directory contains no .pkl files: {model_text}")
        return
    if "flownet.pkl" not in pkl_files:
        add_warning(
            warnings,
            "model directory has .pkl files but not flownet.pkl; the current fallback model.RIFE loader expects flownet.pkl",
        )


def validate_script(script_text: str, repo_root: Optional[Path], errors: List[str]) -> None:
    script_path = existing_path(script_text, repo_root)
    if not script_path.is_file():
        add_error(errors, f"source script not found: {script_text}")


def validate_numeric_png_dir(img_dir_text: str, repo_root: Optional[Path], errors: List[str], warnings: List[str]) -> None:
    img_dir = check_dir("PNG frame directory", img_dir_text, repo_root, errors)
    if img_dir is None:
        return
    pngs = sorted(p for p in img_dir.iterdir() if p.is_file() and "png" in p.name)
    if not pngs:
        add_error(errors, f"PNG frame directory contains no lowercase 'png' files: {img_dir_text}")
        return
    numeric = []
    non_numeric = []
    for path in pngs:
        stem = path.name[:-4] if path.name.lower().endswith(".png") else path.stem
        if stem.isdigit():
            numeric.append(int(stem))
        else:
            non_numeric.append(path.name)
    if non_numeric:
        add_error(
            errors,
            "PNG frame names must have integer stems for inference_video.py sorting; non-numeric examples: "
            + ", ".join(non_numeric[:5]),
        )
    if numeric:
        numeric_sorted = sorted(numeric)
        expected = list(range(numeric_sorted[0], numeric_sorted[-1] + 1))
        if numeric_sorted != expected:
            missing = sorted(set(expected) - set(numeric_sorted))
            add_warning(
                warnings,
                "PNG numeric sequence has gaps; first missing indices: " + ", ".join(str(i) for i in missing[:10]),
            )
        if numeric_sorted[0] != 0:
            add_warning(warnings, "PNG numeric sequence does not start at 0; this can be okay but verify intended order")


def command_to_text(parts: Sequence[str]) -> str:
    return shlex.join([str(part) for part in parts])


def maybe_add(parts: List[str], flag: str, value: Optional[object]) -> None:
    if value is not None:
        parts.extend([flag, str(value)])


def build_image_command(args: argparse.Namespace) -> Tuple[List[str], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else None

    if args.validate:
        validate_script(args.script, repo_root, errors)
        check_file("first image", args.img[0], repo_root, errors)
        check_file("second image", args.img[1], repo_root, errors)
        validate_model_dir(args.model, repo_root, errors, warnings)

    if args.ratio is not None:
        if not 0 <= args.ratio <= 1:
            add_error(errors, "--ratio must be between 0 and 1")
        elif args.ratio == 0:
            add_warning(warnings, "--ratio 0 is parsed but source ratio mode is disabled by a falsey zero value")
        elif args.ratio == 1:
            add_warning(warnings, "--ratio 1 will select or nearly select the second endpoint")
    if args.rthreshold <= 0:
        add_error(errors, "--rthreshold must be positive")
    if args.rmaxcycles < 1:
        add_error(errors, "--rmaxcycles must be at least 1")

    command: List[str] = [args.python, args.script, "--img", args.img[0], args.img[1]]
    if args.ratio is None:
        command.extend(["--exp", str(args.exp)])
    else:
        command.extend(["--ratio", str(args.ratio), "--rthreshold", str(args.rthreshold), "--rmaxcycles", str(args.rmaxcycles)])
    command.extend(["--model", args.model])
    return command, errors, warnings


def build_video_command(args: argparse.Namespace) -> Tuple[List[str], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else None

    if args.video is None and args.img is None:
        add_error(errors, "either --video or --img is required for the video subcommand")
    if args.video is not None and args.img is not None:
        add_error(errors, "use either --video or --img, not both; the source behavior is ambiguous when both are supplied")
    if args.scale not in VALID_SCALES:
        add_error(errors, "--scale must be one of 0.25, 0.5, 1.0, 2.0, 4.0")
    if args.fps is not None and args.fps <= 0:
        add_error(errors, "--fps must be positive")
    if args.ext.startswith("."):
        add_warning(warnings, "--ext should usually omit the leading dot, for example 'mp4' not '.mp4'")
    if args.skip:
        add_warning(warnings, "--skip is abandoned by the current source script and should not be relied on")
    if args.fp16:
        add_warning(warnings, "--fp16 is intended for suitable CUDA/Tensor Core devices; disable it for CPU or dtype issues")
    if args.UHD and args.scale == 1.0:
        add_warning(warnings, "source will change --scale from 1.0 to 0.5 because --UHD is set")
    if args.img is not None and not args.png:
        add_warning(warnings, "source forces --png when --img is supplied")
    if args.video is not None and (args.png or args.fps is not None):
        add_warning(warnings, "audio will not be merged when --png is used or --fps is manually supplied")

    if args.validate:
        validate_script(args.script, repo_root, errors)
        validate_model_dir(args.model, repo_root, errors, warnings)
        if args.video is not None:
            check_file("input video", args.video, repo_root, errors)
        if args.img is not None:
            validate_numeric_png_dir(args.img, repo_root, errors, warnings)
        if args.output:
            output_path = resolve_for_validation(args.output, repo_root)
            if output_path is not None and output_path.parent and not output_path.parent.exists():
                add_error(errors, f"output parent directory does not exist: {args.output}")

    command: List[str] = [args.python, args.script]
    maybe_add(command, "--video", args.video)
    maybe_add(command, "--output", args.output)
    maybe_add(command, "--img", args.img)
    if args.montage:
        command.append("--montage")
    command.extend(["--model", args.model])
    if args.fp16:
        command.append("--fp16")
    if args.UHD:
        command.append("--UHD")
    command.extend(["--scale", str(args.scale)])
    if args.skip:
        command.append("--skip")
    maybe_add(command, "--fps", args.fps)
    if args.png:
        command.append("--png")
    command.extend(["--ext", args.ext, "--exp", str(args.exp)])
    return command, errors, warnings


def add_global_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--python", default=os.environ.get("PYTHON", "python"), help="Python executable token to put in the printed command (default: %(default)s).")
    parser.add_argument("--repo-root", help="Optional checkout root used only to resolve relative paths during validation.")
    parser.add_argument("--validate", action="store_true", help="Validate source script, inputs, and checkpoint directory before printing the command.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build safe ECCV2022-RIFE image/video interpolation commands without running inference.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_global_args(parser)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    image = subparsers.add_parser("image", help="Build an inference_img.py command for two input images.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    image.add_argument("--script", default="inference_img.py", help="Path/token for the source image inference script.")
    image.add_argument("--img", nargs=2, required=True, metavar=("IMG0", "IMG1"), help="Two input image paths.")
    image.add_argument("--exp", type=positive_int, default=4, help="Recursive midpoint exponent for fixed-factor interpolation.")
    image.add_argument("--ratio", type=float, help="Optional arbitrary timestep between 0 and 1; when set, the source ignores --exp.")
    image.add_argument("--rthreshold", type=float, default=0.02, help="Tolerance for ratio bisection mode.")
    image.add_argument("--rmaxcycles", type=positive_int, default=8, help="Maximum bisection cycles for ratio mode.")
    image.add_argument("--model", default="train_log", help="Checkpoint directory to pass to --model.")
    image.set_defaults(builder=build_image_command)

    video = subparsers.add_parser("video", help="Build an inference_video.py command for a video file or numbered PNG directory.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    video.add_argument("--script", default="inference_video.py", help="Path/token for the source video inference script.")
    video.add_argument("--video", help="Input video path.")
    video.add_argument("--output", help="Output video path.")
    video.add_argument("--img", help="Directory of numerically named PNG frames.")
    video.add_argument("--montage", action="store_true", help="Request source montage mode.")
    video.add_argument("--model", default="train_log", help="Checkpoint directory to pass to --model.")
    video.add_argument("--fp16", action="store_true", help="Request source FP16 mode on CUDA.")
    video.add_argument("--UHD", action="store_true", help="Request source UHD helper, which sets scale to 0.5 when scale is 1.0.")
    video.add_argument("--scale", type=float, default=1.0, help="Processing scale: 0.25, 0.5, 1.0, 2.0, or 4.0.")
    video.add_argument("--skip", action="store_true", help="Include deprecated source --skip flag.")
    video.add_argument("--fps", type=int, help="Explicit output FPS; disables source audio merge.")
    video.add_argument("--png", action="store_true", help="Write vid_out/*.png instead of a video file.")
    video.add_argument("--ext", default="mp4", help="Output extension token for derived video outputs.")
    video.add_argument("--exp", type=positive_int, default=1, help="Interpolation factor exponent; factor is 2**exp.")
    video.set_defaults(builder=build_video_command)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command, errors, warnings = args.builder(args)

    for warning in warnings:
        print(warning, file=sys.stderr)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("No command emitted because validation failed.", file=sys.stderr)
        return 2

    print(command_to_text(command))
    print("# Dry run only: this helper did not execute inference.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
