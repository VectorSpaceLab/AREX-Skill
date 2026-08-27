#!/usr/bin/env python3
"""Validate common RobustVideoMatting training dataset directory layouts.

The checks are intentionally lightweight: they inspect paths and a few filename
relationships, but never download data, decode videos, import torch, or start
training. Use --strict to return non-zero when any provided dataset root fails.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _path(value: str | None) -> Path | None:
    return Path(value).expanduser().resolve() if value else None


def _sample_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS])


def _sample_dirs(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


def check_videomatte(label: str, root: Path | None) -> dict[str, Any]:
    result = {"label": label, "kind": "videomatte", "provided": bool(root), "ok": True, "errors": [], "warnings": []}
    if root is None:
        return result
    fgr = root / "fgr"
    pha = root / "pha"
    if not root.is_dir():
        result["errors"].append(f"root is not a directory: {root}")
    if not fgr.is_dir():
        result["errors"].append("missing fgr/ directory")
    if not pha.is_dir():
        result["errors"].append("missing pha/ directory")
    if fgr.is_dir() and pha.is_dir():
        fgr_clips = _sample_dirs(fgr)
        pha_clips = _sample_dirs(pha)
        if not fgr_clips:
            result["errors"].append("fgr/ contains no clip directories")
        missing = sorted(set(fgr_clips[:20]) - set(pha_clips))
        if missing:
            result["errors"].append(f"pha/ missing clip directories matching fgr/: {missing[:5]}")
        if fgr_clips:
            clip = fgr_clips[0]
            fgr_frames = _sample_files(fgr / clip)
            pha_frames = _sample_files(pha / clip)
            if not fgr_frames:
                result["errors"].append(f"fgr/{clip}/ contains no image frames")
            frame_missing = sorted(set(fgr_frames[:20]) - set(pha_frames))
            if frame_missing:
                result["errors"].append(f"pha/{clip}/ missing frames matching fgr/{clip}/: {frame_missing[:5]}")
    result["ok"] = not result["errors"]
    return result


def check_imagematte(label: str, root: Path | None) -> dict[str, Any]:
    result = {"label": label, "kind": "imagematte", "provided": bool(root), "ok": True, "errors": [], "warnings": []}
    if root is None:
        return result
    fgr = root / "fgr"
    pha = root / "pha"
    if not root.is_dir():
        result["errors"].append(f"root is not a directory: {root}")
    if not fgr.is_dir():
        result["errors"].append("missing fgr/ directory")
    if not pha.is_dir():
        result["errors"].append("missing pha/ directory")
    if fgr.is_dir() and pha.is_dir():
        fgr_files = _sample_files(fgr)
        pha_files = _sample_files(pha)
        if not fgr_files:
            result["errors"].append("fgr/ contains no image files")
        missing = sorted(set(fgr_files[:50]) - set(pha_files))
        if missing:
            result["errors"].append(f"pha/ missing files matching fgr/: {missing[:10]}")
    result["ok"] = not result["errors"]
    return result


def check_background_images(label: str, root: Path | None) -> dict[str, Any]:
    result = {"label": label, "kind": "background-images", "provided": bool(root), "ok": True, "errors": [], "warnings": []}
    if root is None:
        return result
    if not root.is_dir():
        result["errors"].append(f"root is not a directory: {root}")
    elif not _sample_files(root):
        result["errors"].append("directory contains no image files")
    result["ok"] = not result["errors"]
    return result


def check_background_videos(label: str, root: Path | None) -> dict[str, Any]:
    result = {"label": label, "kind": "background-videos", "provided": bool(root), "ok": True, "errors": [], "warnings": []}
    if root is None:
        return result
    if not root.is_dir():
        result["errors"].append(f"root is not a directory: {root}")
    else:
        clips = _sample_dirs(root)
        if not clips:
            result["errors"].append("directory contains no clip subdirectories")
        else:
            frames = _sample_files(root / clips[0])
            if not frames:
                result["errors"].append(f"first clip {clips[0]!r} contains no image frames")
    result["ok"] = not result["errors"]
    return result


def check_file(label: str, kind: str, path: Path | None) -> dict[str, Any]:
    result = {"label": label, "kind": kind, "provided": bool(path), "ok": True, "errors": [], "warnings": []}
    if path is not None and not path.is_file():
        result["errors"].append(f"file not found: {path}")
    result["ok"] = not result["errors"]
    return result


def check_dir(label: str, kind: str, path: Path | None) -> dict[str, Any]:
    result = {"label": label, "kind": kind, "provided": bool(path), "ok": True, "errors": [], "warnings": []}
    if path is not None and not path.is_dir():
        result["errors"].append(f"directory not found: {path}")
    result["ok"] = not result["errors"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate RobustVideoMatting dataset layout paths without running training.")
    parser.add_argument("--videomatte-train")
    parser.add_argument("--videomatte-valid")
    parser.add_argument("--imagematte-train")
    parser.add_argument("--imagematte-valid")
    parser.add_argument("--background-images-train")
    parser.add_argument("--background-images-valid")
    parser.add_argument("--background-videos-train")
    parser.add_argument("--background-videos-valid")
    parser.add_argument("--coco-imgdir")
    parser.add_argument("--coco-anndir")
    parser.add_argument("--coco-annfile")
    parser.add_argument("--spd-imgdir")
    parser.add_argument("--spd-segdir")
    parser.add_argument("--youtubevis-videodir")
    parser.add_argument("--youtubevis-annfile")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when any provided check fails.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a text summary.")
    args = parser.parse_args()

    checks = [
        check_videomatte("videomatte.train", _path(args.videomatte_train)),
        check_videomatte("videomatte.valid", _path(args.videomatte_valid)),
        check_imagematte("imagematte.train", _path(args.imagematte_train)),
        check_imagematte("imagematte.valid", _path(args.imagematte_valid)),
        check_background_images("background_images.train", _path(args.background_images_train)),
        check_background_images("background_images.valid", _path(args.background_images_valid)),
        check_background_videos("background_videos.train", _path(args.background_videos_train)),
        check_background_videos("background_videos.valid", _path(args.background_videos_valid)),
        check_dir("coco_panoptic.imgdir", "coco-images", _path(args.coco_imgdir)),
        check_dir("coco_panoptic.anndir", "coco-annotations-dir", _path(args.coco_anndir)),
        check_file("coco_panoptic.annfile", "coco-annotations-json", _path(args.coco_annfile)),
        check_dir("spd.imgdir", "spd-images", _path(args.spd_imgdir)),
        check_dir("spd.segdir", "spd-segments", _path(args.spd_segdir)),
        check_dir("youtubevis.videodir", "youtubevis-images", _path(args.youtubevis_videodir)),
        check_file("youtubevis.annfile", "youtubevis-json", _path(args.youtubevis_annfile)),
    ]
    provided = [c for c in checks if c["provided"]]
    payload = {"ok": all(c["ok"] for c in provided), "checks": provided, "provided_count": len(provided)}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if not provided:
            print("No dataset paths were provided; pass one or more --*-path options to validate a layout.")
        for c in provided:
            status = "OK" if c["ok"] else "FAIL"
            print(f"[{status}] {c['label']} ({c['kind']})")
            for err in c["errors"]:
                print(f"  error: {err}")
            for warn in c["warnings"]:
                print(f"  warning: {warn}")

    return 1 if args.strict and not payload["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
