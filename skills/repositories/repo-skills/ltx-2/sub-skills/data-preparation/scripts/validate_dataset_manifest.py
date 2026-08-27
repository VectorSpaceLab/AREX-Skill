#!/usr/bin/env python3
"""Validate an LTX dataset manifest without running captioning, encoding, or network work."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CANONICAL_COLUMNS = {
    "caption",
    "video",
    "audio",
    "reference_video",
    "reference_audio",
    "video_mask",
    "audio_mask",
}
ALIASES = {"media_path": "video", "ref_media_path": "reference_video"}
PATH_ROLES = {
    "video",
    "audio",
    "reference_video",
    "reference_audio",
    "video_mask",
    "audio_mask",
}
TARGET_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}
TARGET_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aac"}
MASK_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".heic", ".heif", ".bmp", ".tiff", ".webp"}
BUCKET_RE = re.compile(r"^(\d+)x(\d+)x(\d+)$")


@dataclass
class Manifest:
    path: Path
    rows: list[dict[str, Any]]
    columns: list[str]


def load_manifest(path: Path) -> Manifest:
    suffix = path.suffix.lower()
    if suffix not in {".json", ".jsonl", ".csv"}:
        raise ValueError(f"Unsupported manifest extension {path.suffix!r}; expected .json, .jsonl, or .csv")
    if not path.is_file():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON manifest must contain a list of objects")
        rows = data
    elif suffix == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                obj = json.loads(stripped)
                if not isinstance(obj, dict):
                    raise ValueError(f"JSONL line {line_no} is not an object")
                rows.append(obj)
    else:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError("CSV manifest is missing a header row")
            rows = [dict(row) for row in reader]

    if not rows:
        raise ValueError("Manifest contains no rows")
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index} is not an object")

    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                columns.append(str(key))
    return Manifest(path=path, rows=rows, columns=columns)


def resolve_roles(
    columns: list[str],
    *,
    caption_column: str | None,
    video_column: str | None,
) -> tuple[dict[str, str], list[str]]:
    notes: list[str] = []
    roles: dict[str, str] = {}
    by_role: dict[str, list[str]] = {}
    for col in columns:
        role = ALIASES.get(col, col)
        if role in CANONICAL_COLUMNS:
            by_role.setdefault(role, []).append(col)

    for role, cols in by_role.items():
        if len(cols) > 1:
            notes.append(f"ambiguous role {role!r}: columns {cols}; use an override or remove one")
        else:
            roles[role] = cols[0]

    if caption_column:
        if caption_column not in columns:
            notes.append(f"caption override column {caption_column!r} is not present")
        else:
            roles["caption"] = caption_column
    if video_column:
        if video_column not in columns:
            notes.append(f"video override column {video_column!r} is not present")
        else:
            roles["video"] = video_column
    return roles, notes


def cell_is_blank(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"nan", "none", "null"}


def parse_buckets(text: str, spatial_factor: int, temporal_factor: int) -> list[tuple[int, int, int]]:
    buckets: list[tuple[int, int, int]] = []
    for raw in text.split(";"):
        item = raw.strip()
        match = BUCKET_RE.match(item)
        if not match:
            raise ValueError(f"Invalid bucket {item!r}; expected WxHxF")
        width, height, frames = map(int, match.groups())
        if width <= 0 or height <= 0 or frames <= 0:
            raise ValueError(f"Bucket dimensions must be positive: {item!r}")
        if width % spatial_factor != 0 or height % spatial_factor != 0:
            raise ValueError(
                f"Bucket {item!r} has width/height not divisible by spatial factor {spatial_factor}"
            )
        if frames % temporal_factor != 1:
            raise ValueError(f"Bucket {item!r} has frames that do not satisfy F % {temporal_factor} == 1")
        buckets.append((width, height, frames))
    if not buckets:
        raise ValueError("No resolution buckets parsed")
    return buckets


def parse_durations(text: str) -> list[float]:
    durations: list[float] = []
    for raw in text.split(";"):
        item = raw.strip()
        if not item:
            continue
        value = float(item)
        if value <= 0:
            raise ValueError(f"Audio duration must be positive: {item!r}")
        durations.append(value)
    if not durations:
        raise ValueError("No audio durations parsed")
    return durations


def resolve_data_path(value: Any, root: Path) -> Path:
    path = Path(str(value).strip()).expanduser()
    return path if path.is_absolute() else root / path


def expected_path_roles(args: argparse.Namespace) -> set[str]:
    roles = set(PATH_ROLES)
    if not args.require_reference_video:
        roles.discard("reference_video")
    if not args.require_reference_audio:
        roles.discard("reference_audio")
    if not args.require_video_mask:
        roles.discard("video_mask")
    if not args.require_audio_mask:
        roles.discard("audio_mask")
    return roles


def validate(args: argparse.Namespace) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    manifest = load_manifest(args.manifest)
    root = args.dataset_root or manifest.path.parent
    roles, role_notes = resolve_roles(manifest.columns, caption_column=args.caption_column, video_column=args.video_column)
    errors.extend(role_notes)

    if "caption" not in roles:
        errors.append("No caption column found; expected 'caption' or use --caption-column")
    if "video" not in roles and "audio" not in roles:
        errors.append("No target media column found; expected 'video', 'media_path', or 'audio'")

    required_roles = {"caption"}
    if args.require_video:
        required_roles.add("video")
    if args.require_audio:
        required_roles.add("audio")
    if args.require_reference_video:
        required_roles.add("reference_video")
    if args.require_reference_audio:
        required_roles.add("reference_audio")
    if args.require_video_mask:
        required_roles.add("video_mask")
    if args.require_audio_mask:
        required_roles.add("audio_mask")

    for role in sorted(required_roles):
        if role not in roles:
            errors.append(f"Required role {role!r} is missing")

    role_counts: dict[str, int] = {role: 0 for role in roles}
    missing_files: list[str] = []
    absolute_paths: list[str] = []
    target_image_count = 0
    target_video_count = 0
    target_unknown_media_count = 0
    audio_count = 0

    for row_index, row in enumerate(manifest.rows, start=1):
        for role, column in roles.items():
            value = row.get(column)
            if role in required_roles or role in {"caption", "video", "audio"}:
                if cell_is_blank(value):
                    errors.append(f"Row {row_index}: required column {column!r} for role {role!r} is blank")
                    continue
            if cell_is_blank(value):
                continue
            role_counts[role] = role_counts.get(role, 0) + 1
            if role in PATH_ROLES:
                text_value = str(value).strip()
                raw_path = Path(text_value).expanduser()
                if raw_path.is_absolute():
                    absolute_paths.append(f"row {row_index} {column}={text_value}")
                resolved = resolve_data_path(text_value, root)
                if args.check_files and not resolved.exists():
                    missing_files.append(f"row {row_index} {column}={text_value}")
                suffix = resolved.suffix.lower()
                if role == "video":
                    if suffix in TARGET_IMAGE_EXTENSIONS:
                        target_image_count += 1
                    elif suffix in TARGET_VIDEO_EXTENSIONS:
                        target_video_count += 1
                    else:
                        target_unknown_media_count += 1
                elif role == "audio" and suffix in AUDIO_EXTENSIONS:
                    audio_count += 1

    if missing_files:
        preview = "; ".join(missing_files[:10])
        extra = "" if len(missing_files) <= 10 else f"; ... {len(missing_files) - 10} more"
        errors.append(f"Missing referenced files: {preview}{extra}")
    if absolute_paths:
        preview = "; ".join(absolute_paths[:5])
        extra = "" if len(absolute_paths) <= 5 else f"; ... {len(absolute_paths) - 5} more"
        warnings.append(f"Manifest uses absolute paths; portability may suffer: {preview}{extra}")

    buckets: list[tuple[int, int, int]] = []
    if args.resolution_buckets:
        try:
            buckets = parse_buckets(args.resolution_buckets, args.spatial_factor, args.temporal_factor)
        except Exception as exc:  # noqa: BLE001 - show validation error cleanly
            errors.append(str(exc))
    elif "video" in roles:
        warnings.append("Video/image manifests require --resolution-buckets before preprocessing")

    if args.audio_durations:
        try:
            parse_durations(args.audio_durations)
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
    elif "audio" in roles and "video" not in roles:
        warnings.append("Audio-only manifests require --audio-durations before preprocessing")

    if target_unknown_media_count:
        warnings.append(
            f"{target_unknown_media_count} target media paths have uncommon extensions; target still images should usually be .png/.jpg/.jpeg"
        )
    if target_image_count and target_video_count:
        if buckets:
            frames = {frames for _width, _height, frames in buckets}
            if 1 not in frames:
                errors.append("Mixed image+video dataset requires at least one F=1 resolution bucket")
            if not any(frames_value > 1 for frames_value in frames):
                errors.append("Mixed image+video dataset requires at least one video bucket with F>1")
            if len(buckets) > 1:
                warnings.append("Multiple buckets/mixed shapes require training batch size 1; route training config to training-workflows")
        else:
            warnings.append("Mixed image+video dataset detected; plan buckets including F=1 and at least one F>1 bucket")
    elif target_image_count and buckets and 1 not in {frames for _width, _height, frames in buckets}:
        errors.append("Image dataset requires an F=1 resolution bucket")
    elif target_video_count and buckets and not any(frames > 1 for _width, _height, frames in buckets):
        errors.append("Video dataset requires at least one resolution bucket with F>1")

    if len(buckets) > 1:
        warnings.append("Multiple resolution buckets imply later training batch size 1")

    if args.strict and warnings:
        errors.extend(f"strict warning: {warning}" for warning in warnings)

    summary = {
        "manifest": str(manifest.path),
        "rows": len(manifest.rows),
        "columns": manifest.columns,
        "roles": roles,
        "role_counts": role_counts,
        "target_images": target_image_count,
        "target_videos": target_video_count,
        "target_unknown_media": target_unknown_media_count,
        "explicit_audio_rows": audio_count,
        "warnings": warnings,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Manifest: {manifest.path}")
        print(f"Rows: {len(manifest.rows)}")
        print("Roles:")
        for role, column in sorted(roles.items()):
            print(f"  {role}: {column} ({role_counts.get(role, 0)} non-empty)")
        print(f"Target media: {target_image_count} images, {target_video_count} videos, {target_unknown_media_count} other")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        if errors:
            print("Errors:")
            for error in errors:
                print(f"  - {error}")
        print("Result: " + ("FAIL" if errors else "PASS"))

    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely validate an LTX CSV/JSON/JSONL dataset manifest without preprocessing media.",
    )
    parser.add_argument("manifest", type=Path, help="CSV, JSON, or JSONL manifest to validate")
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=None,
        help="Base directory for resolving relative paths; defaults to the manifest directory",
    )
    parser.add_argument("--caption-column", default=None, help="Column to treat as caption instead of auto-detected caption")
    parser.add_argument("--video-column", default=None, help="Column to treat as target video/media instead of video/media_path")
    parser.add_argument(
        "--no-check-files",
        dest="check_files",
        action="store_false",
        help="Only validate schema and non-empty path cells; do not require files to exist",
    )
    parser.set_defaults(check_files=True)
    parser.add_argument("--resolution-buckets", default=None, help='Optional bucket string such as "960x544x1;960x544x49"')
    parser.add_argument("--audio-durations", default=None, help='Optional audio duration buckets such as "2.0;4.0;8.0"')
    parser.add_argument("--spatial-factor", type=int, default=32, help="Video VAE spatial factor for bucket validation")
    parser.add_argument("--temporal-factor", type=int, default=8, help="Video VAE temporal factor for bucket validation")
    parser.add_argument("--require-video", action="store_true", help="Require a target video/media column")
    parser.add_argument("--require-audio", action="store_true", help="Require an explicit audio column")
    parser.add_argument("--require-reference-video", action="store_true", help="Require reference_video/ref_media_path")
    parser.add_argument("--require-reference-audio", action="store_true", help="Require reference_audio")
    parser.add_argument("--require-video-mask", action="store_true", help="Require video_mask")
    parser.add_argument("--require-audio-mask", action="store_true", help="Require audio_mask")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return validate(args)
    except Exception as exc:  # noqa: BLE001 - command-line utility should fail cleanly
        if args.json:
            print(json.dumps({"errors": [str(exc)], "warnings": []}, indent=2), file=sys.stdout)
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
