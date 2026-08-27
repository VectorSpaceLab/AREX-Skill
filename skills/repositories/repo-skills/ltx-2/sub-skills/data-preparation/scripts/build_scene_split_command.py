#!/usr/bin/env python3
"""Build a safe LTX split_scenes.py command without splitting video."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path

DURATION_RE = re.compile(r"^(\d+(?:\.\d+)?s|\d+|\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)$")


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def validate_duration(value: str | None, label: str, errors: list[str]) -> None:
    if value is not None and not DURATION_RE.match(value):
        errors.append(f"{label}={value!r} should be frames (123), seconds (123s), or HH:MM:SS[.nnn]")


def build_prefix(args: argparse.Namespace) -> list[str]:
    if args.runner == "uv":
        return ["uv", "run", "python"]
    return [args.python_executable]


def script_path(args: argparse.Namespace) -> str:
    script = Path(args.split_scenes_script) if args.split_scenes_script else Path(__file__).with_name("split_scenes.py")
    if args.repo_root and not script.is_absolute():
        return str((args.repo_root / script).resolve())
    return str(script)


def command_parts(args: argparse.Namespace) -> list[str]:
    parts = build_prefix(args)
    parts.append(script_path(args))
    parts.extend([str(args.video_path), str(args.output_dir)])
    if args.detector != "content":
        parts.extend(["--detector", args.detector])
    if args.threshold is not None:
        parts.extend(["--threshold", str(args.threshold)])
    if args.max_scenes is not None:
        parts.extend(["--max-scenes", str(args.max_scenes)])
    if args.min_scene_length is not None:
        parts.extend(["--min-scene-length", str(args.min_scene_length)])
    if args.filter_shorter_than is not None:
        parts.extend(["--filter-shorter-than", args.filter_shorter_than])
    if args.skip_start is not None:
        parts.extend(["--skip-start", str(args.skip_start)])
    if args.skip_end is not None:
        parts.extend(["--skip-end", str(args.skip_end)])
    if args.duration is not None:
        parts.extend(["-d", args.duration])
    if args.save_images is not None:
        parts.extend(["--save-images", str(args.save_images)])
    if args.stats_file is not None:
        parts.extend(["--stats-file", str(args.stats_file)])
    if args.luma_only:
        parts.append("--luma-only")
    if args.adaptive_window is not None:
        parts.extend(["--adaptive-window", str(args.adaptive_window)])
    if args.fade_bias is not None:
        parts.extend(["--fade-bias", str(args.fade_bias)])
    if args.downscale is not None:
        parts.extend(["--downscale", str(args.downscale)])
    if args.frame_skip is not None:
        parts.extend(["--frame-skip", str(args.frame_skip)])
    return parts


def validate_plan(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if args.check_input and not args.video_path.is_file():
        errors.append(f"Input video does not exist: {args.video_path}")
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.allow_existing_output:
        warnings.append("Output directory already exists and is non-empty; confirm before running or choose a fresh directory")
    if args.stats_file and args.stats_file.exists() and not args.allow_existing_output:
        warnings.append("Stats file already exists; running split_scenes may overwrite or append depending on script behavior")
    if args.save_images and args.save_images > 0:
        warnings.append("--save-images creates additional preview image files in the output area")
    if args.max_scenes is not None and args.max_scenes <= 0:
        errors.append("--max-scenes must be positive")
    if args.min_scene_length is not None and args.min_scene_length <= 0:
        errors.append("--min-scene-length must be positive")
    if args.save_images is not None and args.save_images < 0:
        errors.append("--save-images must be non-negative")
    if args.skip_start is not None and args.skip_start < 0:
        errors.append("--skip-start must be non-negative")
    if args.skip_end is not None and args.skip_end < 0:
        errors.append("--skip-end must be non-negative")
    if args.downscale is not None and args.downscale <= 0:
        errors.append("--downscale must be positive")
    if args.frame_skip is not None and args.frame_skip < 0:
        errors.append("--frame-skip must be non-negative")
    if args.fade_bias is not None and not (-1.0 <= args.fade_bias <= 1.0):
        errors.append("--fade-bias should be between -1.0 and 1.0")
    validate_duration(args.filter_shorter_than, "--filter-shorter-than", errors)
    validate_duration(args.duration, "--duration", errors)

    if not args.filter_shorter_than:
        warnings.append("No --filter-shorter-than was provided; very short scenes may be saved and later skipped by frame buckets")
    if args.duration or args.max_scenes:
        warnings.append("Command limits the split scope; ensure this is intentional for full dataset preparation")
    if not args.dry_run_notice_off:
        warnings.append("This builder only prints the command; running the printed command will write split clips")
    return errors, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Construct a split_scenes.py command and surface file-safety warnings. The command is printed but not run.",
    )
    parser.add_argument("video_path", type=Path, help="Input video to split")
    parser.add_argument("output_dir", type=Path, help="Directory where split scene clips would be written")
    parser.add_argument("--detector", choices=["content", "adaptive", "threshold", "histogram"], default="content")
    parser.add_argument("--threshold", type=float, default=None)
    parser.add_argument("--max-scenes", type=int, default=None)
    parser.add_argument("--min-scene-length", type=int, default=None, help="Minimum scene length during detection, in frames")
    parser.add_argument("--filter-shorter-than", default=None, help="Filter saved scenes shorter than frames, seconds, or timecode")
    parser.add_argument("--skip-start", type=int, default=None)
    parser.add_argument("--skip-end", type=int, default=None)
    parser.add_argument("--duration", "-d", default=None, help="Limit how much of the video to process")
    parser.add_argument("--save-images", type=int, default=None, help="Number of preview images to save per scene")
    parser.add_argument("--stats-file", type=Path, default=None)
    parser.add_argument("--luma-only", action="store_true")
    parser.add_argument("--adaptive-window", type=int, default=None)
    parser.add_argument("--fade-bias", type=float, default=None)
    parser.add_argument("--downscale", type=int, default=None)
    parser.add_argument("--frame-skip", type=int, default=None)
    parser.add_argument("--runner", choices=["uv", "python"], default="uv")
    parser.add_argument("--python-executable", default="python")
    parser.add_argument(
        "--split-scenes-script",
        default=None,
        help="Path to split_scenes.py in the printed command; defaults to the bundled helper in this skill tree",
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional repository root used to resolve relative script path")
    parser.add_argument("--no-check-input", dest="check_input", action="store_false", help="Do not require the input video to exist")
    parser.set_defaults(check_input=True)
    parser.add_argument("--allow-existing-output", action="store_true", help="Suppress warnings about non-empty output dirs/stats files")
    parser.add_argument("--dry-run-notice-off", action="store_true", help="Suppress reminder that this builder does not split video")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        errors, warnings = validate_plan(args)
        parts = command_parts(args)
        shell_command = shell_join(parts)
    except Exception as exc:  # noqa: BLE001
        if args.json:
            print(json.dumps({"errors": [str(exc)], "warnings": []}, indent=2))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {"command": parts, "shell_command": shell_command, "warnings": warnings, "errors": errors},
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print("Command:")
        print(shell_command)
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  - {warning}")
        if errors:
            print("\nErrors:")
            for error in errors:
                print(f"  - {error}")
        print("\nResult: " + ("FAIL" if errors else "PASS"))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
