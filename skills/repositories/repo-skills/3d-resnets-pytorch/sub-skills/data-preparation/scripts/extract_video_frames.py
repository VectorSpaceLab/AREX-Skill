#!/usr/bin/env python3
"""Extract RGB JPEG frames in the layout expected by 3D-ResNets-PyTorch.

This is a self-contained adaptation of the repository's generate_video_jpgs.py.
It intentionally does not import from the original checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Optional

DATASET_VIDEO_EXT = {
    "kinetics": ".mp4",
    "mit": ".mp4",
    "activitynet": ".mp4",
    "ucf101": ".avi",
    "hmdb51": ".avi",
}


def positive_jobs(value: int) -> int:
    if value == -1:
        return max(1, os.cpu_count() or 1)
    return max(1, value)


def check_tools() -> None:
    missing = [tool for tool in ("ffmpeg", "ffprobe") if shutil.which(tool) is None]
    if missing:
        raise SystemExit(
            "Missing required tool(s) on PATH: "
            + ", ".join(missing)
            + ". Install FFmpeg/FFprobe or fix PATH before extracting frames."
        )


def parse_rate(rate_text: str | None) -> Optional[float]:
    if not rate_text or rate_text in {"0/0", "N/A"}:
        return None
    try:
        return float(Fraction(rate_text))
    except Exception:
        try:
            return float(rate_text)
        except Exception:
            return None


def ffprobe_info(video_path: Path) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate,r_frame_rate,duration,nb_frames",
        "-of",
        "json",
        str(video_path),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {video_path}: {proc.stderr.strip()}")
    payload = json.loads(proc.stdout or "{}")
    streams = payload.get("streams") or []
    if not streams:
        raise RuntimeError(f"ffprobe found no video stream in {video_path}")
    stream = streams[0]
    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)
    fps = parse_rate(stream.get("avg_frame_rate")) or parse_rate(stream.get("r_frame_rate"))
    duration = None
    try:
        duration = float(stream.get("duration"))
    except Exception:
        pass
    n_frames = None
    try:
        if stream.get("nb_frames") not in (None, "N/A"):
            n_frames = int(stream.get("nb_frames"))
    except Exception:
        n_frames = None
    if n_frames is None and fps and duration:
        n_frames = int(round(fps * duration))
    return {"width": width, "height": height, "fps": fps, "duration": duration, "n_frames": n_frames}


def count_existing_frames(dst_dir: Path) -> int:
    if not dst_dir.exists():
        return 0
    return sum(1 for p in dst_dir.iterdir() if p.suffix.lower() == ".jpg" and p.name.startswith("image_"))


def scale_filter(width: int, height: int, size: int, fps: int) -> str:
    if width > height:
        vf = f"scale=-1:{size}"
    else:
        vf = f"scale={size}:-1"
    if fps > 0:
        # The original utility used minterpolate. For data preparation, a plain
        # fps filter is safer and preserves the requested output frame rate.
        vf += f",fps={fps}"
    return vf


def iter_video_jobs(src_dir: Path, dst_dir: Path, dataset: str, ext: str) -> Iterable[tuple[Path, Path]]:
    if dataset == "activitynet":
        for video_path in sorted(src_dir.iterdir()):
            if video_path.is_file() and video_path.suffix.lower() == ext:
                yield video_path, dst_dir
        return

    for class_dir in sorted(p for p in src_dir.iterdir() if p.is_dir()):
        dst_class_dir = dst_dir / class_dir.name
        for video_path in sorted(class_dir.iterdir()):
            if video_path.is_file() and video_path.suffix.lower() == ext:
                yield video_path, dst_class_dir


def extract_one(
    video_path: Path,
    dst_parent: Path,
    *,
    fps: int,
    size: int,
    overwrite: bool,
    dry_run: bool,
) -> tuple[str, str]:
    info = ffprobe_info(video_path)
    if not info["width"] or not info["height"]:
        return "skipped", f"{video_path}: ffprobe returned invalid dimensions"

    dst_video_dir = dst_parent / video_path.stem
    expected = info.get("n_frames")
    existing = count_existing_frames(dst_video_dir)
    if expected and existing >= expected and not overwrite:
        return "skipped", f"{video_path}: {existing} existing frames >= expected {expected}"

    if dry_run:
        return "planned", f"{video_path} -> {dst_video_dir}/image_%05d.jpg"

    dst_video_dir.mkdir(parents=True, exist_ok=True)
    if overwrite:
        for frame in dst_video_dir.glob("image_*.jpg"):
            frame.unlink()

    vf = scale_filter(info["width"], info["height"], size, fps)
    output_pattern = str(dst_video_dir / "image_%05d.jpg")
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        vf,
        "-threads",
        "1",
        output_pattern,
    ]
    subprocess.run(cmd, check=True)
    produced = count_existing_frames(dst_video_dir)
    return "ok", f"{video_path} -> {dst_video_dir} ({produced} frames)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract RGB JPEG frames for 3D-ResNets-PyTorch data loaders."
    )
    parser.add_argument("dir_path", type=Path, help="Raw video directory")
    parser.add_argument("dst_path", type=Path, help="Destination frame root")
    parser.add_argument(
        "dataset",
        choices=sorted(DATASET_VIDEO_EXT),
        help="Dataset layout/ext convention: kinetics|mit|activitynet use mp4; ucf101|hmdb51 use avi",
    )
    parser.add_argument("--n_jobs", "--n-jobs", default=1, type=int, help="Parallel video jobs; -1 uses all CPUs")
    parser.add_argument("--fps", default=-1, type=int, help="Output frame rate; -1 keeps the decoded rate")
    parser.add_argument("--size", default=240, type=int, help="Short-side frame size used by FFmpeg scale")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate existing image_*.jpg files")
    parser.add_argument("--dry-run", action="store_true", help="List planned conversions without running FFmpeg")
    args = parser.parse_args(argv)

    check_tools()
    if not args.dir_path.is_dir():
        parser.error(f"dir_path is not a directory: {args.dir_path}")

    ext = DATASET_VIDEO_EXT[args.dataset]
    jobs = list(iter_video_jobs(args.dir_path, args.dst_path, args.dataset, ext))
    if not jobs:
        raise SystemExit(
            f"No {ext} videos found for dataset={args.dataset}. Check the dataset-specific raw layout."
        )

    args.dst_path.mkdir(parents=True, exist_ok=True)
    n_workers = positive_jobs(args.n_jobs)
    counts = {"ok": 0, "skipped": 0, "planned": 0, "failed": 0}

    if n_workers == 1:
        for video_path, dst_parent in jobs:
            try:
                status, message = extract_one(video_path, dst_parent, fps=args.fps, size=args.size, overwrite=args.overwrite, dry_run=args.dry_run)
            except Exception as exc:  # noqa: BLE001 - report all conversion failures
                status, message = "failed", f"{video_path}: {exc}"
            counts[status] = counts.get(status, 0) + 1
            print(f"[{status}] {message}")
    else:
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            future_map = {
                pool.submit(extract_one, video_path, dst_parent, fps=args.fps, size=args.size, overwrite=args.overwrite, dry_run=args.dry_run): video_path
                for video_path, dst_parent in jobs
            }
            for future in as_completed(future_map):
                try:
                    status, message = future.result()
                except Exception as exc:  # noqa: BLE001
                    status, message = "failed", f"{future_map[future]}: {exc}"
                counts[status] = counts.get(status, 0) + 1
                print(f"[{status}] {message}")

    print("summary:", counts)
    return 1 if counts.get("failed") else 0


if __name__ == "__main__":
    sys.exit(main())
