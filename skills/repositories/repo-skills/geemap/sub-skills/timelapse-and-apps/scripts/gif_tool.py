#!/usr/bin/env python3
"""Safe local GIF helpers for the geemap timelapse-and-apps skill.

This CLI is intentionally local-file-only. It never initializes Earth Engine and never
requests remote imagery. Commands that annotate GIFs or convert GIFs to MP4 import
``geemap.timelapse`` lazily and call only local GIF utilities.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _size(value: str) -> tuple[int, int]:
    normalized = value.lower().replace(",", "x")
    parts = normalized.split("x")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("size must be WIDTHxHEIGHT, for example 96x64")
    width = _positive_int(parts[0])
    height = _positive_int(parts[1])
    return width, height


def _xy(value: str) -> tuple[int, int] | tuple[str, str]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2 or not all(parts):
        raise argparse.ArgumentTypeError("xy must be X,Y, for example 10,12 or 4%,6%")

    parsed: list[int | str] = []
    percent_mode: bool | None = None
    for part in parts:
        if part.endswith("%"):
            try:
                number = float(part[:-1])
            except ValueError as exc:
                raise argparse.ArgumentTypeError(f"invalid percentage coordinate {part!r}") from exc
            if number < 0 or number > 100:
                raise argparse.ArgumentTypeError("percentage coordinates must be between 0% and 100%")
            parsed.append(f"{number:g}%")
            current_percent = True
        else:
            parsed.append(_positive_or_zero_int(part))
            current_percent = False
        if percent_mode is None:
            percent_mode = current_percent
        elif percent_mode != current_percent:
            raise argparse.ArgumentTypeError("xy coordinates must both be pixels or both be percentages")

    if percent_mode:
        return (str(parsed[0]), str(parsed[1]))
    return (int(parsed[0]), int(parsed[1]))


def _positive_or_zero_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer coordinate, got {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("pixel coordinates must be non-negative")
    return parsed


def _ensure_input_gif(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"input GIF does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"input GIF is not a file: {path}")
    if path.suffix.lower() != ".gif":
        raise ValueError(f"input file must end with .gif: {path}")


def _ensure_output_parent(path: Path) -> None:
    parent = path.parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def _gif_info(path: Path) -> dict[str, Any]:
    try:
        from PIL import Image, ImageSequence
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("Pillow is required for GIF inspection and fixture creation") from exc

    _ensure_input_gif(path)
    try:
        with Image.open(path) as image:
            durations: list[int | None] = []
            for frame in ImageSequence.Iterator(image):
                durations.append(frame.info.get("duration"))
            return {
                "path": str(path),
                "format": image.format,
                "width": image.size[0],
                "height": image.size[1],
                "frames": getattr(image, "n_frames", len(durations) or 1),
                "is_animated": bool(getattr(image, "is_animated", False)),
                "duration_ms": durations,
                "loop": image.info.get("loop"),
            }
    except Exception as exc:
        raise RuntimeError(f"failed to inspect GIF {path}: {exc}") from exc


def _load_geemap_timelapse():
    try:
        from geemap.timelapse import add_text_to_gif, gif_to_mp4
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "Could not import geemap.timelapse. Install geemap with its base "
            "dependencies before using annotate or to-mp4. This tool did not "
            "attempt any Earth Engine operation."
        ) from exc
    return add_text_to_gif, gif_to_mp4


def _text_sequence_from_args(args: argparse.Namespace, frame_count: int) -> int | str | list[str] | None:
    if args.text is not None:
        return args.text
    if args.start_number is not None:
        return args.start_number
    if args.text_sequence is not None:
        labels = [item.strip() for item in args.text_sequence.split(",")]
        if any(label == "" for label in labels):
            raise ValueError("--text-sequence must not contain empty labels")
        if len(labels) != frame_count:
            raise ValueError(
                f"--text-sequence has {len(labels)} labels but the input GIF has {frame_count} frames"
            )
        return labels
    return None


def cmd_inspect(args: argparse.Namespace) -> int:
    info = _gif_info(args.input)
    if args.json:
        print(json.dumps(info, indent=2, sort_keys=True))
    else:
        print(f"path: {info['path']}")
        print(f"format: {info['format']}")
        print(f"size: {info['width']}x{info['height']}")
        print(f"frames: {info['frames']}")
        print(f"animated: {info['is_animated']}")
        if info.get("loop") is not None:
            print(f"loop: {info['loop']}")
        durations = info.get("duration_ms") or []
        if durations:
            unique = sorted({duration for duration in durations if duration is not None})
            print(f"duration_ms_unique: {unique}")
    return 0


def cmd_fixture(args: argparse.Namespace) -> int:
    try:
        from PIL import Image, ImageDraw
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("Pillow is required for fixture creation") from exc

    if args.output.suffix.lower() != ".gif":
        raise ValueError("fixture output must end with .gif")
    _ensure_output_parent(args.output)

    width, height = args.size
    palette = [
        (28, 90, 164),
        (35, 145, 88),
        (226, 135, 67),
        (146, 80, 164),
        (190, 61, 65),
        (80, 150, 170),
    ]
    frames = []
    for index in range(args.frames):
        image = Image.new("RGB", (width, height), palette[index % len(palette)])
        draw = ImageDraw.Draw(image)
        label = f"{index + 1}/{args.frames}"
        draw.rectangle((4, 4, min(width - 4, 56), min(height - 4, 24)), fill=(0, 0, 0))
        draw.text((8, 8), label, fill=(255, 255, 255))
        frames.append(image)

    frames[0].save(
        args.output,
        save_all=True,
        append_images=frames[1:],
        duration=args.duration,
        loop=args.loop,
        optimize=True,
    )
    print(f"created fixture GIF: {args.output}")
    return 0


def cmd_annotate(args: argparse.Namespace) -> int:
    _ensure_input_gif(args.input)
    if args.output.suffix.lower() != ".gif":
        raise ValueError("annotate output must end with .gif")
    _ensure_output_parent(args.output)

    info = _gif_info(args.input)
    text_sequence = _text_sequence_from_args(args, int(info["frames"]))
    duration = args.duration
    if duration is None:
        durations = [value for value in (info.get("duration_ms") or []) if value is not None]
        duration = durations[0] if durations else 100

    add_text_to_gif, _gif_to_mp4 = _load_geemap_timelapse()
    add_text_to_gif(
        str(args.input),
        str(args.output),
        xy=args.xy,
        text_sequence=text_sequence,
        font_type=args.font_type,
        font_size=args.font_size,
        font_color=args.font_color,
        add_progress_bar=args.progress_bar,
        progress_bar_color=args.progress_bar_color,
        progress_bar_height=args.progress_bar_height,
        duration=duration,
        loop=args.loop,
    )

    if not args.output.exists():
        raise RuntimeError("geemap.add_text_to_gif returned without creating the output GIF")
    print(f"wrote annotated GIF: {args.output}")
    return 0


def cmd_to_mp4(args: argparse.Namespace) -> int:
    _ensure_input_gif(args.input)
    _ensure_output_parent(args.output)
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required for GIF-to-MP4 conversion but was not found on PATH")

    _add_text_to_gif, gif_to_mp4 = _load_geemap_timelapse()
    gif_to_mp4(str(args.input), str(args.output))

    output = args.output if args.output.suffix.lower() == ".mp4" else args.output.with_suffix(args.output.suffix + ".mp4")
    if args.output.exists():
        output = args.output
    if not output.exists():
        # geemap appends .mp4 when no suffix is supplied; check that case too.
        appended = Path(str(args.output) + ".mp4")
        if appended.exists():
            output = appended
        else:
            raise RuntimeError("geemap.gif_to_mp4 returned without creating the MP4 output")
    print(f"wrote MP4: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local GIF helper for geemap timelapse outputs. No Earth Engine calls are made.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="inspect an existing GIF")
    inspect_parser.add_argument("input", type=Path, help="input .gif file")
    inspect_parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    inspect_parser.set_defaults(func=cmd_inspect)

    fixture_parser = subparsers.add_parser("fixture", help="create a tiny local test GIF")
    fixture_parser.add_argument("output", type=Path, help="output .gif file")
    fixture_parser.add_argument("--frames", type=_positive_int, default=4, help="number of frames (default: 4)")
    fixture_parser.add_argument("--size", type=_size, default=(96, 64), help="WIDTHxHEIGHT (default: 96x64)")
    fixture_parser.add_argument("--duration", type=_positive_int, default=120, help="frame duration in ms (default: 120)")
    fixture_parser.add_argument("--loop", type=int, default=0, help="GIF loop count, 0 means forever (default: 0)")
    fixture_parser.set_defaults(func=cmd_fixture)

    annotate_parser = subparsers.add_parser("annotate", help="add text/progress bar to an existing GIF")
    annotate_parser.add_argument("input", type=Path, help="input .gif file")
    annotate_parser.add_argument("output", type=Path, help="output .gif file")
    text_group = annotate_parser.add_mutually_exclusive_group()
    text_group.add_argument("--text", help="single label repeated on every frame")
    text_group.add_argument("--text-sequence", help="comma-separated labels, one per frame")
    text_group.add_argument("--start-number", type=int, help="number the first frame with this integer")
    annotate_parser.add_argument("--xy", type=_xy, default=("5%", "5%"), help="text location X,Y as pixels or percentages (default: 5%,5%)")
    annotate_parser.add_argument("--font-type", default="arial.ttf", help="font name or font file path (default: arial.ttf)")
    annotate_parser.add_argument("--font-size", type=_positive_int, default=20, help="font size (default: 20)")
    annotate_parser.add_argument("--font-color", default="#000000", help="font color name or hex color (default: #000000)")
    annotate_parser.add_argument("--progress-bar", dest="progress_bar", action="store_true", default=True, help="add progress bar (default)")
    annotate_parser.add_argument("--no-progress-bar", dest="progress_bar", action="store_false", help="do not add progress bar")
    annotate_parser.add_argument("--progress-bar-color", default="white", help="progress bar color (default: white)")
    annotate_parser.add_argument("--progress-bar-height", type=_positive_int, default=5, help="progress bar height in pixels (default: 5)")
    annotate_parser.add_argument("--duration", type=_positive_int, help="frame duration in ms; defaults to input metadata or 100")
    annotate_parser.add_argument("--loop", type=int, default=0, help="GIF loop count, 0 means forever (default: 0)")
    annotate_parser.set_defaults(func=cmd_annotate)

    mp4_parser = subparsers.add_parser("to-mp4", help="convert a GIF to MP4 with geemap/ffmpeg")
    mp4_parser.add_argument("input", type=Path, help="input .gif file")
    mp4_parser.add_argument("output", type=Path, help="output .mp4 file")
    mp4_parser.set_defaults(func=cmd_to_mp4)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
