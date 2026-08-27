#!/usr/bin/env python3
"""Build a safe LTX process_dataset.py command without running preprocessing."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any

ALIASES = {"media_path": "video", "ref_media_path": "reference_video"}
KNOWN_ROLES = {"caption", "video", "audio", "reference_video", "reference_audio", "video_mask", "audio_mask"}
TARGET_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
TARGET_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
BUCKET_RE = re.compile(r"^(\d+)x(\d+)x(\d+)$")


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def read_rows(path: Path) -> list[dict[str, Any]] | None:
    if not path.is_file():
        return None
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else None
        if suffix == ".jsonl":
            rows: list[dict[str, Any]] = []
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if stripped:
                        obj = json.loads(stripped)
                        if isinstance(obj, dict):
                            rows.append(obj)
            return rows
        if suffix == ".csv":
            with path.open("r", encoding="utf-8", newline="") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
    except Exception:
        return None
    return None


def detect_roles(rows: list[dict[str, Any]] | None, *, caption_column: str | None, video_column: str | None) -> dict[str, str]:
    columns: list[str] = []
    seen: set[str] = set()
    if rows:
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    columns.append(str(key))
    roles: dict[str, str] = {}
    for col in columns:
        role = ALIASES.get(col, col)
        if role in KNOWN_ROLES and role not in roles:
            roles[role] = col
    if caption_column:
        roles["caption"] = caption_column
    if video_column:
        roles["video"] = video_column
    return roles


def parse_buckets(text: str | None, spatial_factor: int, temporal_factor: int) -> list[tuple[int, int, int]]:
    if not text:
        return []
    buckets: list[tuple[int, int, int]] = []
    for raw in text.split(";"):
        item = raw.strip()
        match = BUCKET_RE.match(item)
        if not match:
            raise ValueError(f"Invalid resolution bucket {item!r}; expected WxHxF")
        width, height, frames = map(int, match.groups())
        if width % spatial_factor != 0 or height % spatial_factor != 0:
            raise ValueError(
                f"Bucket {item!r} width/height must be divisible by spatial factor {spatial_factor}"
            )
        if frames % temporal_factor != 1:
            raise ValueError(f"Bucket {item!r} frames must satisfy F % {temporal_factor} == 1")
        buckets.append((width, height, frames))
    return buckets


def parse_durations(text: str | None) -> list[float]:
    if not text:
        return []
    durations = [float(item.strip()) for item in text.split(";") if item.strip()]
    if any(value <= 0 for value in durations):
        raise ValueError("Audio durations must be positive")
    return durations


def infer_media_mix(rows: list[dict[str, Any]] | None, video_column: str | None) -> tuple[int, int, int]:
    if not rows or not video_column:
        return (0, 0, 0)
    images = videos = other = 0
    for row in rows:
        value = row.get(video_column)
        if value is None or str(value).strip() == "":
            continue
        suffix = Path(str(value).strip()).suffix.lower()
        if suffix in TARGET_IMAGE_EXTENSIONS:
            images += 1
        elif suffix in TARGET_VIDEO_EXTENSIONS:
            videos += 1
        else:
            other += 1
    return (images, videos, other)


def build_prefix(args: argparse.Namespace) -> list[str]:
    if args.accelerate_num_processes:
        if args.runner == "uv":
            return ["uv", "run", "accelerate", "launch", "--num_processes", str(args.accelerate_num_processes)]
        return ["accelerate", "launch", "--num_processes", str(args.accelerate_num_processes)]
    if args.runner == "uv":
        return ["uv", "run", "python"]
    return [args.python_executable]


def script_path(args: argparse.Namespace) -> str:
    script = Path(args.process_dataset_script) if args.process_dataset_script else Path(__file__).with_name("process_dataset.py")
    if args.repo_root and not script.is_absolute():
        return str((args.repo_root / script).resolve())
    return str(script)


def add_optional(parts: list[str], flag: str, value: str | int | None) -> None:
    if value is not None:
        parts.extend([flag, str(value)])


def command_parts(args: argparse.Namespace) -> list[str]:
    parts = build_prefix(args)
    parts.append(script_path(args))
    parts.append(str(args.dataset_path))
    add_optional(parts, "--resolution-buckets", args.resolution_buckets)
    parts.extend(["--model-path", str(args.model_path)])
    parts.extend(["--text-encoder-path", str(args.text_encoder_path)])
    add_optional(parts, "--video-vae-path", args.video_vae_path)
    add_optional(parts, "--audio-vae-path", args.audio_vae_path)
    add_optional(parts, "--caption-column", args.caption_column)
    add_optional(parts, "--video-column", args.video_column)
    if args.batch_size != 1:
        parts.extend(["--batch-size", str(args.batch_size)])
    if args.device != "cuda":
        parts.extend(["--device", args.device])
    if args.vae_tiling:
        parts.append("--vae-tiling")
    add_optional(parts, "--output-dir", args.output_dir)
    add_optional(parts, "--lora-trigger", args.lora_trigger)
    if args.decode:
        parts.append("--decode")
    if args.remove_llm_prefixes:
        parts.append("--remove-llm-prefixes")
    if args.skip_audio:
        parts.append("--skip-audio")
    add_optional(parts, "--audio-durations", args.audio_durations)
    if args.load_text_encoder_in_8bit:
        parts.append("--load-text-encoder-in-8bit")
    if args.reference_downscale_factor != 1:
        parts.extend(["--reference-downscale-factor", str(args.reference_downscale_factor)])
    if args.reference_temporal_scale_factor != 1:
        parts.extend(["--reference-temporal-scale-factor", str(args.reference_temporal_scale_factor)])
    if args.overwrite:
        parts.append("--overwrite")
    return parts


def validate_plan(args: argparse.Namespace) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    rows = read_rows(args.dataset_path)
    roles = detect_roles(rows, caption_column=args.caption_column, video_column=args.video_column)

    layout = args.layout
    if layout == "auto":
        layout = "split" if args.video_vae_path or args.audio_vae_path else "unified"

    if rows is None:
        warnings.append("Manifest could not be inspected; command was built from flags only")
    elif not rows:
        errors.append("Manifest appears empty")
    else:
        if "caption" not in roles:
            errors.append("Manifest does not expose a caption column; use --caption-column or rename to caption")
        if "video" not in roles and "audio" not in roles:
            errors.append("Manifest does not expose target media; expected video/media_path or audio")

    has_video = "video" in roles or bool(args.video_column) or args.assume_video
    has_audio = "audio" in roles or args.assume_audio
    has_reference_video = "reference_video" in roles
    has_reference_audio = "reference_audio" in roles

    try:
        buckets = parse_buckets(args.resolution_buckets, args.spatial_factor, args.temporal_factor)
    except Exception as exc:  # noqa: BLE001
        buckets = []
        errors.append(str(exc))

    try:
        durations = parse_durations(args.audio_durations)
    except Exception as exc:  # noqa: BLE001
        durations = []
        errors.append(str(exc))

    if has_video and not args.resolution_buckets:
        errors.append("Video/image manifests require --resolution-buckets")
    if not has_video and has_audio and not args.audio_durations:
        warnings.append("Audio-only preprocessing requires --audio-durations")

    if layout == "split":
        if not args.video_vae_path:
            errors.append("--layout split requires --video-vae-path")
        if not args.audio_vae_path:
            errors.append("--layout split requires --audio-vae-path for full dataset preprocessing")
    elif args.video_vae_path or args.audio_vae_path:
        warnings.append("VAE paths were supplied while --layout unified was selected; verify this is intentional")

    if args.skip_audio:
        warnings.append("--skip-audio disables auto-extracted target audio; do not use for audio-training modes")
        if has_audio or has_reference_audio:
            warnings.append("Manifest has explicit audio/reference_audio; --skip-audio only affects auto-extraction from target video")

    if len(buckets) > 1:
        warnings.append("Multiple resolution buckets require later training batch size 1")

    if buckets and rows is not None:
        images, videos, other = infer_media_mix(rows, roles.get("video"))
        frame_values = {frames for _width, _height, frames in buckets}
        if images and 1 not in frame_values:
            errors.append("Image rows require at least one F=1 bucket")
        if videos and not any(frames > 1 for frames in frame_values):
            errors.append("Video rows require at least one F>1 bucket")
        if images and videos:
            warnings.append("Mixed image+video dataset detected; include F=1 and F>1 buckets and set training batch size 1")
        if other:
            warnings.append(f"{other} target media rows have uncommon extensions")

    if has_reference_video:
        if args.reference_downscale_factor > 1 and len(buckets) > 1:
            errors.append("--reference-downscale-factor > 1 supports only a single resolution bucket")
        if args.reference_temporal_scale_factor > 1 and len(buckets) > 1:
            errors.append("--reference-temporal-scale-factor > 1 supports only a single resolution bucket")
        if args.reference_downscale_factor > 1 and buckets:
            for width, height, _frames in buckets:
                scaled_width = width // args.reference_downscale_factor
                scaled_height = height // args.reference_downscale_factor
                if width % args.reference_downscale_factor or height % args.reference_downscale_factor:
                    errors.append(
                        f"Reference downscale factor {args.reference_downscale_factor} does not evenly divide {width}x{height}"
                    )
                elif scaled_width % args.spatial_factor or scaled_height % args.spatial_factor:
                    errors.append(
                        f"Scaled reference bucket {scaled_width}x{scaled_height} is not divisible by spatial factor {args.spatial_factor}"
                    )
        if args.reference_temporal_scale_factor > 1 and buckets:
            for _width, _height, frames in buckets:
                if (frames - 1) % args.reference_temporal_scale_factor:
                    errors.append(
                        f"Frame count {frames} is incompatible with reference temporal scale {args.reference_temporal_scale_factor}"
                    )
                else:
                    scaled_frames = 1 + (frames - 1) // args.reference_temporal_scale_factor
                    if scaled_frames % args.temporal_factor != 1:
                        errors.append(
                            f"Reference temporal scale yields {scaled_frames} frames, not F % {args.temporal_factor} == 1"
                        )
    elif args.reference_downscale_factor != 1 or args.reference_temporal_scale_factor != 1:
        warnings.append("Reference scale flags were supplied but no reference_video column was detected")

    if args.output_dir and not args.overwrite:
        warnings.append("Existing outputs in --output-dir will be reused/skipped unless --overwrite is added")
    if args.overwrite:
        warnings.append("--overwrite will replace existing cached .pt outputs; confirm stale-data replacement is intended")
    if args.decode:
        warnings.append("--decode performs heavy VAE decoding; use only after explicit approval")
    if args.accelerate_num_processes and args.accelerate_num_processes < 1:
        errors.append("--accelerate-num-processes must be positive")

    metadata = {
        "layout": layout,
        "roles": roles,
        "rows_inspected": None if rows is None else len(rows),
        "buckets": buckets,
        "audio_durations": durations,
        "has_video": has_video,
        "has_audio": has_audio,
        "has_reference_video": has_reference_video,
        "has_reference_audio": has_reference_audio,
    }
    return errors, warnings, metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Construct an LTX process_dataset.py command and warn about unsafe or inconsistent flags. The command is printed but not run.",
    )
    parser.add_argument("dataset_path", type=Path, help="Dataset CSV/JSON/JSONL path to pass to process_dataset.py")
    parser.add_argument("--layout", choices=["auto", "unified", "split"], default="auto", help="Checkpoint layout for VAE flag validation")
    parser.add_argument("--model-path", required=True, help="Unified checkpoint or split transformer safetensors path")
    parser.add_argument("--text-encoder-path", required=True, help="Matching Gemma/text-encoder path")
    parser.add_argument("--video-vae-path", default=None, help="Split-pack video VAE path")
    parser.add_argument("--audio-vae-path", default=None, help="Split-pack audio VAE path")
    parser.add_argument("--resolution-buckets", default=None, help='Resolution buckets, e.g. "960x544x1;960x544x49"')
    parser.add_argument("--audio-durations", default=None, help='Audio duration buckets, e.g. "2.0;4.0;8.0"')
    parser.add_argument("--caption-column", default=None, help="Caption column override")
    parser.add_argument("--video-column", default=None, help="Target video/media column override")
    parser.add_argument("--batch-size", type=int, default=1, help="Preprocessing batch size")
    parser.add_argument("--device", default="cuda", help="Device flag to pass through")
    parser.add_argument("--vae-tiling", action="store_true", help="Add --vae-tiling")
    parser.add_argument("--output-dir", default=None, help="Precomputed output root")
    parser.add_argument("--lora-trigger", default=None, help="Trigger token to prepend during caption embedding")
    parser.add_argument("--decode", action="store_true", help="Add --decode; this is heavy and warning-producing")
    parser.add_argument("--remove-llm-prefixes", action="store_true", help="Add --remove-llm-prefixes")
    parser.add_argument("--skip-audio", action="store_true", help="Add --skip-audio")
    parser.add_argument("--load-text-encoder-in-8bit", action="store_true", help="Add --load-text-encoder-in-8bit")
    parser.add_argument("--reference-downscale-factor", type=int, default=1, help="Reference video spatial downscale factor")
    parser.add_argument("--reference-temporal-scale-factor", type=int, default=1, help="Reference video temporal scale factor")
    parser.add_argument("--overwrite", action="store_true", help="Add --overwrite")
    parser.add_argument("--accelerate-num-processes", type=int, default=None, help="Wrap with accelerate launch using this many processes")
    parser.add_argument("--runner", choices=["uv", "python"], default="uv", help="Command runner prefix")
    parser.add_argument("--python-executable", default="python", help="Python executable when --runner python")
    parser.add_argument(
        "--process-dataset-script",
        default=None,
        help="Path to process_dataset.py in the command; defaults to the bundled helper in this skill tree",
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional repository root used to resolve relative script path in the printed command")
    parser.add_argument("--spatial-factor", type=int, default=32, help="VAE spatial factor used for static bucket checks")
    parser.add_argument("--temporal-factor", type=int, default=8, help="VAE temporal factor used for static bucket checks")
    parser.add_argument("--assume-video", action="store_true", help="Assume the manifest has video media if it cannot be inspected")
    parser.add_argument("--assume-audio", action="store_true", help="Assume the manifest has audio media if it cannot be inspected")
    parser.add_argument("--json", action="store_true", help="Emit JSON with command array, shell command, warnings, and errors")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        errors, warnings, metadata = validate_plan(args)
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
                {
                    "command": parts,
                    "shell_command": shell_command,
                    "warnings": warnings,
                    "errors": errors,
                    "metadata": metadata,
                },
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
