#!/usr/bin/env python3
"""Validate Fast Style Transfer video stylization inputs safely.

This helper checks checkpoint/input/output paths, device and batch options,
optional moviepy/ffmpeg availability, and optional video metadata. It never
restores checkpoints, processes frames, or writes output video.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate transform_video.py inputs without processing frames.")
    parser.add_argument("--checkpoint", required=True, help="Checkpoint directory or checkpoint path/prefix.")
    parser.add_argument("--in-path", required=True, help="Input video path.")
    parser.add_argument("--out-path", required=True, help="Output video path.")
    parser.add_argument("--tmp-dir", default=None, help="Optional tmp dir parser compatibility check; not used by inspected main path.")
    parser.add_argument("--device", default="/gpu:0", help="TensorFlow device string such as /gpu:0 or /cpu:0.")
    parser.add_argument("--batch-size", type=int, default=4, help="Frame batch size; must be positive.")
    parser.add_argument("--no-disk", default=False, help="Parser compatibility option; inspected main path does not use it.")
    parser.add_argument("--check-dependencies", action="store_true", help="Check moviepy and ffmpeg/imageio-ffmpeg availability.")
    parser.add_argument("--probe-video", action="store_true", help="Open input with moviepy to read metadata without writing output.")
    return parser


def _dependency_report() -> Dict[str, Any]:
    report: Dict[str, Any] = {"moviepy": None, "imageio_ffmpeg": None, "ffmpeg_executable": shutil.which("ffmpeg")}
    try:
        import moviepy  # type: ignore
        report["moviepy"] = {"ok": True, "version": getattr(moviepy, "__version__", None)}
    except Exception as exc:
        report["moviepy"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    try:
        import imageio_ffmpeg  # type: ignore
        report["imageio_ffmpeg"] = {"ok": True, "exe": imageio_ffmpeg.get_ffmpeg_exe()}
    except Exception as exc:
        report["imageio_ffmpeg"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return report


def _probe_video(path: Path) -> Dict[str, Any]:
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip  # type: ignore
        clip = VideoFileClip(str(path), audio=False)
        try:
            return {"ok": True, "size": list(clip.size), "fps": clip.fps, "duration": clip.duration}
        finally:
            clip.close()
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checkpoint = Path(args.checkpoint).expanduser()
    in_path = Path(args.in_path).expanduser()
    out_path = Path(args.out_path).expanduser()
    report: Dict[str, Any] = {"ok": True, "errors": [], "warnings": [], "paths": {}, "dependencies": None, "video_probe": None}

    report["paths"]["checkpoint"] = {"path": str(args.checkpoint), "exists": checkpoint.exists(), "is_dir": checkpoint.is_dir() if checkpoint.exists() else None}
    if not checkpoint.exists():
        report["errors"].append("checkpoint path does not exist")
    report["paths"]["in_path"] = {"path": str(args.in_path), "exists": in_path.exists(), "is_file": in_path.is_file() if in_path.exists() else None}
    if not in_path.exists() or not in_path.is_file():
        report["errors"].append("input video path must be an existing file")
    parent = out_path.parent if str(out_path.parent) else Path(".")
    report["paths"]["out_parent"] = {"path": str(parent), "exists": parent.exists(), "is_dir": parent.is_dir() if parent.exists() else None}
    if not parent.exists() or not parent.is_dir():
        report["errors"].append("output parent directory does not exist")
    if args.tmp_dir:
        tmp = Path(args.tmp_dir).expanduser()
        report["paths"]["tmp_dir"] = {"path": str(args.tmp_dir), "exists": tmp.exists(), "note": "parsed by wrapper but not used by inspected main path"}
        report["warnings"].append("--tmp-dir is parsed by transform_video.py but not used by the inspected direct ffwd_video path")
    if str(args.no_disk).lower() not in {"false", "true", "0", "1"}:
        report["warnings"].append("--no-disk is parsed as a bool-like value but not used by the inspected main path")
    if args.batch_size <= 0:
        report["errors"].append("batch-size must be positive")
    if not (args.device.startswith("/cpu") or args.device.startswith("/gpu")):
        report["warnings"].append("device string is unusual for this TensorFlow script")

    if args.check_dependencies:
        report["dependencies"] = _dependency_report()
        deps = report["dependencies"]
        if deps["moviepy"] and not deps["moviepy"].get("ok"):
            report["errors"].append("moviepy import failed")
        if not deps.get("ffmpeg_executable") and deps["imageio_ffmpeg"] and not deps["imageio_ffmpeg"].get("ok"):
            report["warnings"].append("no ffmpeg executable or imageio_ffmpeg fallback found")
    if args.probe_video and in_path.exists() and in_path.is_file():
        report["video_probe"] = _probe_video(in_path)
        if not report["video_probe"].get("ok"):
            report["errors"].append("moviepy could not open input video for metadata")

    report["ok"] = not report["errors"]
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
