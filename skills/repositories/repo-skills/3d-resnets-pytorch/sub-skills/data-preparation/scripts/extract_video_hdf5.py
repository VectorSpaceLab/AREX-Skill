#!/usr/bin/env python3
"""Convert raw RGB videos to HDF5 files for 3D-ResNets-PyTorch.

This is a self-contained adaptation of the repository's generate_video_hdf5.py.
It writes HDF5 files with a variable-length uint8 dataset named ``video``;
that is the format consumed by the repository's RGB HDF5 loader. It does not
create optical-flow ``video_u``/``video_v`` datasets.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Optional

import h5py
import numpy as np

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
            + ". Install FFmpeg/FFprobe or fix PATH before extracting HDF5."
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


def scale_filter(width: int, height: int, size: int, fps: int) -> str:
    if width > height:
        vf = f"scale=-1:{size}"
    else:
        vf = f"scale={size}:-1"
    if fps > 0:
        vf += f",fps={fps}"
    return vf


def iter_video_jobs(src_dir: Path, dst_dir: Path, dataset: str, ext: str) -> Iterable[tuple[Path, Path, str | None]]:
    if dataset == "activitynet":
        for video_path in sorted(src_dir.iterdir()):
            if video_path.is_file() and video_path.suffix.lower() == ext:
                yield video_path, dst_dir, None
        return

    for class_dir in sorted(p for p in src_dir.iterdir() if p.is_dir()):
        dst_class_dir = dst_dir / class_dir.name
        for video_path in sorted(class_dir.iterdir()):
            if video_path.is_file() and video_path.suffix.lower() == ext:
                yield video_path, dst_class_dir, class_dir.name


def hashed_fallback_path(dst_parent: Path, stem: str, max_stem_chars: int) -> Path:
    digest = hashlib.sha1(stem.encode("utf-8")).hexdigest()[:12]
    safe_stem = stem[:max_stem_chars].rstrip("._- ") or "video"
    return dst_parent / f"{safe_stem}_{digest}.hdf5"


def is_name_too_long(exc: OSError) -> bool:
    if getattr(exc, "errno", None) == errno.ENAMETOOLONG:
        return True
    text = " ".join(str(arg) for arg in getattr(exc, "args", ()))
    return "errno = 36" in text or "File name too long" in text


def write_hdf5_from_frames(frame_paths: list[Path], hdf5_path: Path) -> None:
    dtype = h5py.special_dtype(vlen=np.dtype("uint8"))
    with h5py.File(hdf5_path, "w") as h5:
        dataset = h5.create_dataset("video", (len(frame_paths),), dtype=dtype)
        for i, frame_path in enumerate(frame_paths):
            dataset[i] = np.frombuffer(frame_path.read_bytes(), dtype="uint8")


def choose_and_write_hdf5(
    frame_paths: list[Path],
    dst_parent: Path,
    stem: str,
    *,
    fallback_stem_chars: int,
) -> tuple[Path, bool]:
    canonical_path = dst_parent / f"{stem}.hdf5"
    try:
        write_hdf5_from_frames(frame_paths, canonical_path)
        return canonical_path, False
    except OSError as exc:
        if not is_name_too_long(exc):
            raise
        fallback = hashed_fallback_path(dst_parent, stem, fallback_stem_chars)
        write_hdf5_from_frames(frame_paths, fallback)
        return fallback, True


def extract_one(
    video_path: Path,
    dst_parent: Path,
    label: str | None,
    *,
    fps: int,
    size: int,
    overwrite: bool,
    dry_run: bool,
    fallback_stem_chars: int,
) -> tuple[str, str, dict | None]:
    canonical_hdf5 = dst_parent / f"{video_path.stem}.hdf5"
    if canonical_hdf5.exists() and not overwrite:
        record = {
            "video_id": video_path.stem,
            "label": label,
            "path": str(canonical_hdf5),
            "canonical_path": str(canonical_hdf5),
            "used_fallback": False,
        }
        return "skipped", f"{video_path}: existing {canonical_hdf5}", record

    info = ffprobe_info(video_path)
    if not info["width"] or not info["height"]:
        return "skipped", f"{video_path}: ffprobe returned invalid dimensions", None

    dst_parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        return "planned", f"{video_path} -> {canonical_hdf5}", None

    if overwrite:
        canonical_hdf5.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory(prefix="3dr_hdf5_frames_") as tmp:
        tmp_dir = Path(tmp)
        vf = scale_filter(info["width"], info["height"], size, fps)
        output_pattern = str(tmp_dir / "image_%05d.jpg")
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
        frame_paths = sorted(tmp_dir.glob("image_*.jpg"))
        if not frame_paths:
            raise RuntimeError(f"ffmpeg produced no frames for {video_path}")
        hdf5_path, used_fallback = choose_and_write_hdf5(
            frame_paths, dst_parent, video_path.stem, fallback_stem_chars=fallback_stem_chars
        )

    record = {
        "video_id": video_path.stem,
        "label": label,
        "path": str(hdf5_path),
        "canonical_path": str(canonical_hdf5),
        "used_fallback": used_fallback,
    }
    flag = " fallback-name" if used_fallback else ""
    return "ok", f"{video_path} -> {hdf5_path} ({len(frame_paths)} frames{flag})", record


def write_manifest(path: Path, dataset: str, dst_path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"dataset": dataset, "video_type": "hdf5", "root": str(dst_path), "items": records}
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract RGB HDF5 video files for 3D-ResNets-PyTorch data loaders."
    )
    parser.add_argument("dir_path", type=Path, help="Raw video directory")
    parser.add_argument("dst_path", type=Path, help="Destination HDF5 root")
    parser.add_argument(
        "dataset",
        choices=sorted(DATASET_VIDEO_EXT),
        help="Dataset layout/ext convention: kinetics|mit|activitynet use mp4; ucf101|hmdb51 use avi",
    )
    parser.add_argument("--n_jobs", "--n-jobs", default=1, type=int, help="Parallel video jobs; -1 uses all CPUs")
    parser.add_argument("--fps", default=-1, type=int, help="Output frame rate; -1 keeps the decoded rate")
    parser.add_argument("--size", default=240, type=int, help="Short-side frame size used by FFmpeg scale")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate existing .hdf5 files")
    parser.add_argument("--dry-run", action="store_true", help="List planned conversions without running FFmpeg")
    parser.add_argument(
        "--fallback-stem-chars",
        default=180,
        type=int,
        help="Maximum original-stem characters retained when a too-long HDF5 filename must be shortened",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Optional JSON manifest recording actual HDF5 paths, including long-name fallbacks",
    )
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
    records: list[dict] = []

    if n_workers == 1:
        for video_path, dst_parent, label in jobs:
            try:
                status, message, record = extract_one(
                    video_path,
                    dst_parent,
                    label,
                    fps=args.fps,
                    size=args.size,
                    overwrite=args.overwrite,
                    dry_run=args.dry_run,
                    fallback_stem_chars=args.fallback_stem_chars,
                )
            except Exception as exc:  # noqa: BLE001
                status, message, record = "failed", f"{video_path}: {exc}", None
            counts[status] = counts.get(status, 0) + 1
            if record is not None:
                records.append(record)
            print(f"[{status}] {message}")
    else:
        with ThreadPoolExecutor(max_workers=n_workers) as pool:
            future_map = {
                pool.submit(
                    extract_one,
                    video_path,
                    dst_parent,
                    label,
                    fps=args.fps,
                    size=args.size,
                    overwrite=args.overwrite,
                    dry_run=args.dry_run,
                    fallback_stem_chars=args.fallback_stem_chars,
                ): video_path
                for video_path, dst_parent, label in jobs
            }
            for future in as_completed(future_map):
                try:
                    status, message, record = future.result()
                except Exception as exc:  # noqa: BLE001
                    status, message, record = "failed", f"{future_map[future]}: {exc}", None
                counts[status] = counts.get(status, 0) + 1
                if record is not None:
                    records.append(record)
                print(f"[{status}] {message}")

    if args.manifest:
        write_manifest(args.manifest, args.dataset, args.dst_path, records)
        print(f"manifest: {args.manifest}")
    print("summary:", counts)
    return 1 if counts.get("failed") else 0


if __name__ == "__main__":
    sys.exit(main())
