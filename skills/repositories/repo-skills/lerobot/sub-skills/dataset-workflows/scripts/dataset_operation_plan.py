#!/usr/bin/env python3
"""Print a non-mutating plan for a LeRobot dataset operation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MUTATING = {
    "delete_episodes",
    "split",
    "merge",
    "remove_feature",
    "modify_tasks",
    "convert_image_to_video",
    "recompute_stats",
    "reencode_videos",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate local dataset/output path intent and print a dry-run plan. "
            "This helper never edits, converts, downloads, uploads, or overwrites."
        )
    )
    parser.add_argument("--source-root", type=Path, required=True, help="Exact source dataset root")
    parser.add_argument(
        "--operation",
        choices=sorted(MUTATING | {"info"}),
        required=True,
        help="Operation to plan, not execute",
    )
    parser.add_argument("--output-root", type=Path, help="Distinct output root for a mutating operation")
    parser.add_argument("--episodes", help="JSON list of episode indices, for example '[0, 2]'")
    parser.add_argument("--features", help="JSON list of feature names, for example '[\"action\"]'")
    parser.add_argument("--splits", help="JSON split mapping, for example '{\"train\":0.8,\"val\":0.2}'")
    parser.add_argument("--allow-existing", action="store_true", help="Acknowledge that output already exists (still no writes)")
    return parser.parse_args()


def error(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def parse_json_arg(raw: str | None, name: str):
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--{name} is not valid JSON: {exc}") from exc


def main() -> int:
    args = parse_args()
    source = args.source_root.expanduser().resolve()
    if not source.is_dir():
        return error(f"source root does not exist: {source}")
    info_path = source / "meta" / "info.json"
    if not info_path.is_file():
        return error(f"missing source metadata: {info_path}")
    try:
        info = load_json(info_path)
        episodes = parse_json_arg(args.episodes, "episodes")
        features = parse_json_arg(args.features, "features")
        splits = parse_json_arg(args.splits, "splits")
    except ValueError as exc:
        return error(str(exc))

    output = args.output_root.expanduser().resolve() if args.output_root else None
    if args.operation in MUTATING:
        if output is None:
            return error(
                f"{args.operation} requires --output-root for a safe plan; "
                "choose a distinct root or explicitly manage an in-place backup"
            )
        if output == source:
            if not args.allow_existing:
                return error("output equals source; pass --allow-existing to acknowledge in-place intent")
            overwrite_note = "in-place intent acknowledged; helper still performs no write"
        elif output.exists() and not args.allow_existing:
            return error("output already exists; choose a new root or pass --allow-existing")
        else:
            overwrite_note = "existing output acknowledged" if output.exists() else "new output root"
    else:
        overwrite_note = "read-only info plan"

    feature_map = info.get("features") if isinstance(info.get("features"), dict) else {}
    video_keys = [k for k, v in feature_map.items() if isinstance(v, dict) and v.get("dtype") == "video"]
    data_files = sorted(str(path.relative_to(source)) for path in (source / "data").glob("*/*.parquet"))
    episode_files = sorted(str(path.relative_to(source)) for path in (source / "meta" / "episodes").glob("*/*.parquet"))
    plan = {
        "dry_run": True,
        "writes_performed": False,
        "downloads_performed": False,
        "uploads_performed": False,
        "operation": args.operation,
        "source_root": str(source),
        "output_root": str(output) if output else None,
        "output_status": overwrite_note,
        "codebase_version": info.get("codebase_version"),
        "fps": info.get("fps"),
        "total_episodes": info.get("total_episodes"),
        "total_frames": info.get("total_frames"),
        "feature_keys": sorted(feature_map),
        "video_keys": video_keys,
        "data_parquet_files": len(data_files),
        "episode_metadata_files": len(episode_files),
        "requested_episodes": episodes,
        "requested_features": features,
        "requested_splits": splits,
        "gates": [
            "validate metadata/data/episode schemas before execution",
            "confirm all referenced video files and decoder/codec support",
            "confirm output is distinct or approve a backed-up overwrite",
            "bound episode/frame batches and disk usage",
            "reload output in a fresh reader and compare counts/features/stats",
        ],
    }
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
