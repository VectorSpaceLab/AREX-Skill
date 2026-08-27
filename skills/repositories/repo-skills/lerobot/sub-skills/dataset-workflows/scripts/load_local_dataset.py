#!/usr/bin/env python3
"""Bounded, read-only inspection of a local LeRobot v3 dataset root."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a local LeRobot dataset without Hub downloads or writes. "
            "The root must contain meta/, data/, and optional videos/."
        )
    )
    parser.add_argument("--root", type=Path, required=True, help="Exact local dataset root")
    parser.add_argument("--repo-id", default="local/inspection", help="Identifier used only by the API")
    parser.add_argument("--limit", type=int, default=3, help="Maximum data rows to inspect (default: 3)")
    parser.add_argument("--episode", type=int, action="append", help="Episode to inspect; repeatable")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Decode at most one item per selected episode after local file preflight",
    )
    parser.add_argument(
        "--no-decode-video",
        action="store_true",
        help="Never decode visual video data; metadata and schema checks still run",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 2


def main() -> int:
    args = parse_args()
    if args.limit < 0:
        return fail("--limit must be non-negative")
    root = args.root.expanduser().resolve()
    info_path = root / "meta" / "info.json"
    if not root.is_dir():
        return fail(f"root does not exist or is not a directory: {root}")
    if not info_path.is_file():
        return fail(f"missing local metadata: {info_path}")
    if not (root / "data").is_dir():
        return fail("missing data/ directory")
    if not list((root / "data").glob("*/*.parquet")):
        return fail("data/ contains no chunk/* parquet file")

    try:
        info = json.loads(info_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"cannot parse meta/info.json: {exc}")

    features = info.get("features")
    if not isinstance(features, dict) or not features:
        return fail("meta/info.json has no non-empty features mapping")
    video_keys = [key for key, value in features.items() if isinstance(value, dict) and value.get("dtype") == "video"]
    episodes_dir = root / "meta" / "episodes"
    episode_files = sorted(episodes_dir.glob("*/*.parquet")) if episodes_dir.is_dir() else []
    total_episodes = int(info.get("total_episodes", 0) or 0)
    total_tasks = int(info.get("total_tasks", 0) or 0)
    if total_episodes > 0 and not episode_files:
        return fail("total_episodes is nonzero but meta/episodes has no parquet file")
    tasks_path = root / "meta" / "tasks.parquet"
    if total_tasks > 0 and not tasks_path.is_file():
        return fail("total_tasks is nonzero but meta/tasks.parquet is missing")

    # Metadata-only inspection is deliberately independent of LeRobot imports.
    print(json.dumps({
        "root": str(root),
        "codebase_version": info.get("codebase_version"),
        "fps": info.get("fps"),
        "total_episodes": info.get("total_episodes"),
        "total_frames": info.get("total_frames"),
        "feature_keys": sorted(features),
        "video_keys": video_keys,
        "data_files": len(list((root / "data").glob("*/*.parquet"))),
        "episode_metadata_files": len(episode_files),
    }, indent=2))

    try:
        from lerobot.datasets import LeRobotDataset, LeRobotDatasetMetadata
    except Exception as exc:
        print(f"IMPORT_STATUS: dataset API unavailable; metadata preflight passed: {exc}")
        return 0

    try:
        meta = LeRobotDatasetMetadata(args.repo_id, root=root, token=False)
        selected = args.episode or list(range(min(meta.total_episodes, max(args.limit, 1))))
        selected = sorted(set(int(ep) for ep in selected))
        if any(ep < 0 or ep >= meta.total_episodes for ep in selected):
            return fail(f"selected episode is outside 0..{meta.total_episodes - 1}")
        missing_videos: list[str] = []
        for ep in selected:
            for key in meta.video_keys:
                path = root / meta.get_video_file_path(ep, key)
                if not path.is_file():
                    missing_videos.append(f"episode={ep} key={key} path={path.relative_to(root)}")
        if missing_videos:
            print("VIDEO_PREFLIGHT: missing referenced files (metadata-only result is still valid)")
            for item in missing_videos[:20]:
                print(f"  - {item}")
            if args.sample and not args.no_decode_video:
                return fail("--sample requested but referenced video files are missing")

        # Avoid constructing a reader that can attempt a download when visual files
        # are incomplete. Image-only roots and complete roots are safe to load.
        complete_for_reader = not missing_videos
        if complete_for_reader:
            dataset = LeRobotDataset(
                args.repo_id,
                root=root,
                episodes=selected or None,
                download_videos=False,
                token=False,
                return_uint8=True,
            )
            print(json.dumps({
                "reader": "LeRobotDataset",
                "selected_episodes": selected,
                "reader_frames": len(dataset),
                "reader_features": sorted(dataset.features),
            }, indent=2))
            if args.sample and not args.no_decode_video:
                # The reader is episode-filtered, so its integer index is relative
                # to the selected episode list rather than the absolute metadata index.
                relative_start = 0
                for ep in selected[: max(1, args.limit)]:
                    row_index = int(meta.episodes[ep]["dataset_from_index"])
                    item = dataset[relative_start]
                    print(json.dumps({
                        "sample_episode": ep,
                        "sample_index": row_index,
                        "keys": sorted(item),
                        "shapes": {key: list(value.shape) for key, value in item.items() if hasattr(value, "shape")},
                        "task": item.get("task"),
                    }, default=str))
                    relative_start += int(meta.episodes[ep]["length"])
        else:
            print("READER_STATUS: skipped because referenced video files are incomplete")
    except Exception as exc:
        print(f"READER_STATUS: failed without network fallback: {type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
