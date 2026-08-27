#!/usr/bin/env python3
"""Generate a SiamMask-compatible VOT metadata JSON from a local VOT directory.

This adapts the repository's data/create_json.py into a bundled, explicit helper.
It reads a VOT2016/VOT2018/VOT2019-style directory containing list.txt,
per-video groundtruth.txt files, and JPG frames, then writes the metadata JSON
used by SiamMask's VOT evaluator. It does not download data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import cv2
except Exception as exc:  # pragma: no cover - reported in main
    cv2 = None
    CV2_ERROR = exc
else:
    CV2_ERROR = None

TAG_NAMES = {
    "VOT2016": ["camera_motion.label", "illum_change.label", "motion_change.label", "size_change.label", "occlusion.label"],
    "VOT2018": ["camera_motion.tag", "illum_change.tag", "motion_change.tag", "size_change.tag", "occlusion.tag"],
    "VOT2019": ["camera_motion.tag", "illum_change.tag", "motion_change.tag", "size_change.tag", "occlusion.tag"],
}
META_KEYS = ["camera_motion", "illum_change", "motion_change", "size_change", "occlusion"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate SiamMask VOT metadata JSON from an existing VOT dataset directory.")
    p.add_argument("--dataset-root", required=True, help="Path to VOT2016/VOT2018/VOT2019 directory containing list.txt.")
    p.add_argument("--dataset-name", default=None, help="Dataset name. Defaults to the dataset-root basename.")
    p.add_argument("--output", required=True, help="Output JSON path, such as data/VOT2019.json.")
    p.add_argument("--overwrite", action="store_true", help="Allow overwriting an existing output file.")
    return p.parse_args()


def read_float_rows(path: Path) -> list[list[float]]:
    return [list(map(float, line.strip().split(','))) for line in path.read_text().splitlines() if line.strip()]


def read_tag_file(video_dir: Path, filename: str, length: int) -> list[int]:
    path = video_dir / filename
    if not path.exists():
        return []
    values = [int(line.strip()) for line in path.read_text().splitlines() if line.strip()]
    return values + [0] * max(0, length - len(values))


def frame_names(video_dir: Path, dataset_root: Path) -> list[str]:
    frames = sorted(video_dir.glob("*.jpg"))
    if not frames:
        frames = sorted((video_dir / "color").glob("*.jpg"))
    return [str(path.relative_to(dataset_root)) for path in frames]


def generate(dataset_root: Path, dataset_name: str) -> dict[str, Any]:
    if cv2 is None:
        raise RuntimeError(f"OpenCV import failed: {CV2_ERROR}")
    list_path = dataset_root / "list.txt"
    if not list_path.exists():
        raise FileNotFoundError(f"missing list.txt: {list_path}")
    videos = [line.strip() for line in list_path.read_text().splitlines() if line.strip()]
    meta: dict[str, Any] = {}
    for video in videos:
        video_dir = dataset_root / video
        gt_path = video_dir / "groundtruth.txt"
        if not gt_path.exists():
            raise FileNotFoundError(f"missing groundtruth: {gt_path}")
        gt = read_float_rows(gt_path)
        imgs = frame_names(video_dir, dataset_root)
        if not imgs:
            raise FileNotFoundError(f"no jpg frames under {video_dir} or {video_dir / 'color'}")
        first = cv2.imread(str(dataset_root / imgs[0]))
        if first is None:
            raise RuntimeError(f"could not read first image: {dataset_root / imgs[0]}")
        entry: dict[str, Any] = {
            "video_dir": video,
            "init_rect": gt[0],
            "img_names": imgs,
            "width": int(first.shape[1]),
            "height": int(first.shape[0]),
            "gt_rect": gt,
        }
        tag_files = TAG_NAMES.get(dataset_name, [])
        for key, tag_file in zip(META_KEYS, tag_files):
            entry[key] = read_tag_file(video_dir, tag_file, len(gt))
        if dataset_name not in TAG_NAMES:
            for key in META_KEYS:
                entry[key] = []
        meta[video] = entry
    return meta


def main() -> int:
    args = parse_args()
    root = Path(args.dataset_root).expanduser().resolve()
    name = args.dataset_name or root.name
    output = Path(args.output).expanduser().resolve()
    if output.exists() and not args.overwrite:
        raise SystemExit(f"output exists; pass --overwrite to replace it: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    data = generate(root, name)
    output.write_text(json.dumps(data, indent=2, sort_keys=True))
    print(f"wrote {output} with {len(data)} videos for {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
