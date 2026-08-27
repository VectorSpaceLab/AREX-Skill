#!/usr/bin/env python3
"""Validate FlashVSR image-sequence or video metadata without loading models.

The checker is read-only: it performs no network access, model download, GPU
allocation, or output write. It can inspect a real input or validate a
synthetic metadata fixture.

Examples:
  python validate_input.py frames_dir --json
  python validate_input.py clip.mp4 --frame-policy preserve-all
  python validate_input.py --width 320 --height 192 --frames 37
  python validate_input.py --geometry-mode prepared --width 1280 \
      --height 768 --frames 33
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Sequence

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
ALIGNMENT = 128
MIN_OUTPUT_FRAMES = 21  # 8 * 3 - 3; gives at least one streaming iteration.


class ValidationError(ValueError):
    """A user-facing input validation error."""


@dataclass(frozen=True)
class InputMetadata:
    kind: str
    width: int
    height: int
    frames: int
    fps: float
    source: str


@dataclass(frozen=True)
class ValidationPlan:
    input_kind: str
    input_width: int
    input_height: int
    input_frames: int
    fps: float
    geometry_mode: str
    scale: float
    scaled_width: int
    scaled_height: int
    target_width: int
    target_height: int
    crop_width: int
    crop_height: int
    frame_policy: str
    pipeline_frames: int
    expected_output_frames: int
    repeated_input_frames: int
    discarded_input_frames: int
    trim_output_frames: int
    input_tensor_shape: list[int]
    expected_output_tensor_shape: list[int]
    warnings: list[str]


def natural_key(path: Path) -> list[object]:
    """Sort numbered frame names as frame2 before frame10."""
    return [
        int(token) if token.isdigit() else token.lower()
        for token in re.split(r"([0-9]+)", path.name)
    ]


def _positive_int(name: str, value: Optional[int]) -> int:
    if value is None or value <= 0:
        raise ValidationError(f"{name} must be a positive integer (got {value!r})")
    return value


def _positive_float(name: str, value: Optional[float], default: float) -> float:
    if value is None:
        return default
    if not math.isfinite(value) or value <= 0:
        raise ValidationError(f"{name} must be finite and > 0 (got {value!r})")
    return float(value)


def inspect_image_directory(path: Path, fps_override: Optional[float]) -> InputMetadata:
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValidationError(
            "Pillow is required to inspect image directories; install pillow or "
            "use --width/--height/--frames metadata mode"
        ) from exc

    images = sorted(
        (entry for entry in path.iterdir() if entry.is_file() and entry.suffix.lower() in IMAGE_EXTENSIONS),
        key=natural_key,
    )
    if not images:
        raise ValidationError(
            f"no PNG/JPEG frames found in image directory: {path}"
        )

    expected_size: Optional[tuple[int, int]] = None
    for frame_path in images:
        try:
            with Image.open(frame_path) as image:
                image.load()
                size = image.size
        except Exception as exc:
            raise ValidationError(f"cannot decode image frame {frame_path.name}: {exc}") from exc
        if expected_size is None:
            expected_size = size
        elif size != expected_size:
            raise ValidationError(
                f"inconsistent frame geometry: {frame_path.name} is "
                f"{size[0]}x{size[1]}, expected {expected_size[0]}x{expected_size[1]}"
            )

    assert expected_size is not None
    return InputMetadata(
        kind="image-directory",
        width=expected_size[0],
        height=expected_size[1],
        frames=len(images),
        fps=_positive_float("fps", fps_override, 30.0),
        source=str(path),
    )


def inspect_video(path: Path, fps_override: Optional[float]) -> InputMetadata:
    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ValidationError(
            f"unsupported file extension {path.suffix!r}; expected one of "
            + ", ".join(sorted(VIDEO_EXTENSIONS))
        )
    try:
        import imageio.v2 as imageio
    except ImportError as exc:
        raise ValidationError(
            "imageio and an available video backend are required to inspect video; "
            "install imageio plus imageio-ffmpeg, or use metadata mode"
        ) from exc

    try:
        reader = imageio.get_reader(str(path))
    except Exception as exc:
        raise ValidationError(f"cannot open video metadata: {exc}") from exc

    try:
        try:
            first = reader.get_data(0)
        except Exception as exc:
            raise ValidationError(f"cannot decode the first video frame: {exc}") from exc
        if getattr(first, "ndim", 0) < 2:
            raise ValidationError(f"first video frame has invalid shape: {getattr(first, 'shape', None)!r}")
        height, width = int(first.shape[0]), int(first.shape[1])

        try:
            metadata = reader.get_meta_data() or {}
        except Exception:
            metadata = {}

        frame_count: Optional[int] = None
        raw_count = metadata.get("nframes")
        if isinstance(raw_count, int) and raw_count > 0:
            frame_count = raw_count
        if frame_count is None:
            try:
                counted = reader.count_frames()
            except Exception as exc:
                raise ValidationError(
                    "video backend cannot determine frame count safely; provide "
                    "--width, --height, --frames, and optional --fps instead "
                    f"({exc})"
                ) from exc
            if isinstance(counted, int) and counted > 0:
                frame_count = counted
        if frame_count is None:
            raise ValidationError("video reports no readable frames")

        metadata_fps = metadata.get("fps")
        fps = _positive_float(
            "fps",
            fps_override if fps_override is not None else (
                float(metadata_fps) if isinstance(metadata_fps, (int, float)) else None
            ),
            30.0,
        )
        return InputMetadata(
            kind="video",
            width=width,
            height=height,
            frames=frame_count,
            fps=fps,
            source=str(path),
        )
    finally:
        try:
            reader.close()
        except Exception:
            pass


def inspect_input(path: Path, fps_override: Optional[float]) -> InputMetadata:
    if not path.exists():
        raise ValidationError(f"input does not exist: {path}")
    if path.is_dir():
        return inspect_image_directory(path, fps_override)
    if path.is_file():
        return inspect_video(path, fps_override)
    raise ValidationError(f"input is neither a regular file nor a directory: {path}")


def metadata_fixture(args: argparse.Namespace) -> InputMetadata:
    supplied = [args.width is not None, args.height is not None, args.frames is not None]
    if not all(supplied):
        raise ValidationError(
            "without INPUT, provide --width, --height, and --frames together"
        )
    return InputMetadata(
        kind="metadata-fixture",
        width=_positive_int("width", args.width),
        height=_positive_int("height", args.height),
        frames=_positive_int("frames", args.frames),
        fps=_positive_float("fps", args.fps, 30.0),
        source="command-line metadata",
    )


def official_frame_plan(frame_count: int) -> tuple[int, int, int, int, int]:
    """Return F, output, repeats, discards, output trim for official floor policy."""
    n = (frame_count + 3) // 8
    output_frames = 8 * n - 3
    if output_frames < MIN_OUTPUT_FRAMES:
        raise ValidationError(
            f"{frame_count} real frames are insufficient for the official streaming "
            f"layout; provide at least {MIN_OUTPUT_FRAMES} frames"
        )
    pipeline_frames = output_frames + 4  # 8n+1
    repeats = max(0, pipeline_frames - frame_count)
    discards = max(0, frame_count - pipeline_frames)
    return pipeline_frames, output_frames, repeats, discards, 0


def preserve_all_frame_plan(frame_count: int) -> tuple[int, int, int, int, int]:
    """Pad to the next output count congruent to 5 mod 8, then trim output."""
    if frame_count < MIN_OUTPUT_FRAMES:
        raise ValidationError(
            f"{frame_count} real frames are insufficient for a verified streaming "
            f"layout; provide at least {MIN_OUTPUT_FRAMES} frames"
        )
    n = math.ceil((frame_count + 3) / 8)
    output_frames = 8 * n - 3
    pipeline_frames = output_frames + 4
    repeats = pipeline_frames - frame_count
    trim = output_frames - frame_count
    return pipeline_frames, output_frames, repeats, 0, trim


def build_plan(
    metadata: InputMetadata,
    *,
    scale: float,
    geometry_mode: str,
    frame_policy: str,
) -> ValidationPlan:
    width = _positive_int("width", metadata.width)
    height = _positive_int("height", metadata.height)
    frame_count = _positive_int("frames", metadata.frames)
    scale = _positive_float("scale", scale, 4.0)
    warnings: list[str] = []

    if geometry_mode == "source":
        scaled_width = int(round(width * scale))
        scaled_height = int(round(height * scale))
        target_width = (scaled_width // ALIGNMENT) * ALIGNMENT
        target_height = (scaled_height // ALIGNMENT) * ALIGNMENT
        if target_width < ALIGNMENT or target_height < ALIGNMENT:
            raise ValidationError(
                f"scaled geometry {scaled_width}x{scaled_height} is too small for "
                f"{ALIGNMENT}-pixel alignment; increase source size or scale"
            )
        crop_width = scaled_width - target_width
        crop_height = scaled_height - target_height
        if crop_width or crop_height:
            warnings.append(
                f"center-crop the x{scale:g} bicubic result by {crop_width} px "
                f"horizontally and {crop_height} px vertically in total"
            )
    elif geometry_mode == "prepared":
        scaled_width, scaled_height = width, height
        if width % ALIGNMENT or height % ALIGNMENT:
            raise ValidationError(
                f"prepared geometry must be divisible by {ALIGNMENT}; got {width}x{height}"
            )
        target_width, target_height = width, height
        crop_width = crop_height = 0
        if scale != 4.0:
            warnings.append("--scale is informational in prepared geometry mode")
    else:  # argparse constrains this; retain a defensive check.
        raise ValidationError(f"unknown geometry mode: {geometry_mode}")

    if scale != 4.0:
        warnings.append(
            f"scale={scale:g} differs from the strongly recommended 4x setting"
        )

    if frame_policy == "official":
        pipeline_frames, output_frames, repeats, discards, trim = official_frame_plan(frame_count)
    elif frame_policy == "preserve-all":
        pipeline_frames, output_frames, repeats, discards, trim = preserve_all_frame_plan(frame_count)
    else:
        raise ValidationError(f"unknown frame policy: {frame_policy}")

    if discards:
        warnings.append(
            f"the official floor policy discards {discards} trailing prepared input frame(s)"
        )
    if output_frames < frame_count and frame_policy == "official":
        warnings.append(
            f"the aligned model output contains {output_frames} frames, "
            f"{frame_count - output_frames} fewer than the source"
        )
    if trim:
        warnings.append(
            f"trim {trim} repeated tail frame(s) from the encoded output after inference"
        )

    return ValidationPlan(
        input_kind=metadata.kind,
        input_width=width,
        input_height=height,
        input_frames=frame_count,
        fps=metadata.fps,
        geometry_mode=geometry_mode,
        scale=scale,
        scaled_width=scaled_width,
        scaled_height=scaled_height,
        target_width=target_width,
        target_height=target_height,
        crop_width=crop_width,
        crop_height=crop_height,
        frame_policy=frame_policy,
        pipeline_frames=pipeline_frames,
        expected_output_frames=output_frames,
        repeated_input_frames=repeats,
        discarded_input_frames=discards,
        trim_output_frames=trim,
        input_tensor_shape=[1, 3, pipeline_frames, target_height, target_width],
        expected_output_tensor_shape=[3, output_frames, target_height, target_width],
        warnings=warnings,
    )


def format_text(metadata: InputMetadata, plan: ValidationPlan) -> str:
    lines = [
        "VALID FlashVSR input plan",
        f"source: {metadata.source}",
        f"input: {metadata.kind}, {plan.input_width}x{plan.input_height}, "
        f"{plan.input_frames} frames @ {plan.fps:g} fps",
        f"geometry: scaled {plan.scaled_width}x{plan.scaled_height} -> "
        f"target {plan.target_width}x{plan.target_height}",
        f"frames: call with F={plan.pipeline_frames} (8n+1); expect "
        f"{plan.expected_output_frames} (8n-3)",
        f"prepared tensor: {plan.input_tensor_shape} bfloat16 in [-1, 1]",
        f"pipeline output: {plan.expected_output_tensor_shape} in [-1, 1]",
        f"input tail: repeat={plan.repeated_input_frames}, "
        f"discard={plan.discarded_input_frames}; output trim={plan.trim_output_frames}",
    ]
    lines.extend(f"warning: {warning}" for warning in plan.warnings)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate FlashVSR image-directory/video metadata and compute the "
            "128-pixel geometry plus 8n+1 streaming-frame plan."
        )
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="image directory or .mp4/.mov/.avi/.mkv video",
    )
    fixture = parser.add_argument_group("synthetic metadata fixture")
    fixture.add_argument("--width", type=int, help="fixture width in pixels")
    fixture.add_argument("--height", type=int, help="fixture height in pixels")
    fixture.add_argument("--frames", type=int, help="fixture frame count")
    parser.add_argument(
        "--fps",
        type=float,
        help="override/fixture FPS (default: metadata FPS, otherwise 30)",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=4.0,
        help="source bicubic scale before center crop (default: 4.0)",
    )
    parser.add_argument(
        "--geometry-mode",
        choices=("source", "prepared"),
        default="source",
        help=(
            "source computes x-scale then floor-crops to 128 multiples; "
            "prepared requires supplied dimensions already be 128-aligned"
        ),
    )
    parser.add_argument(
        "--frame-policy",
        choices=("official", "preserve-all"),
        default="official",
        help=(
            "official floors to the repository recipe; preserve-all pads to the "
            "next valid output length and reports post-inference trimming"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a machine-readable validation record",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        metadata_flags = any(
            value is not None for value in (args.width, args.height, args.frames)
        )
        if args.input and metadata_flags:
            raise ValidationError(
                "choose either INPUT inspection or --width/--height/--frames metadata mode"
            )
        if args.input:
            metadata = inspect_input(Path(args.input), args.fps)
        else:
            metadata = metadata_fixture(args)
        plan = build_plan(
            metadata,
            scale=args.scale,
            geometry_mode=args.geometry_mode,
            frame_policy=args.frame_policy,
        )
    except ValidationError as exc:
        if args.json:
            print(json.dumps({"valid": False, "error": str(exc)}, indent=2))
        else:
            print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    if args.json:
        record = {"valid": True, "source": metadata.source, **asdict(plan)}
        print(json.dumps(record, indent=2, sort_keys=True))
    else:
        print(format_text(metadata, plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
