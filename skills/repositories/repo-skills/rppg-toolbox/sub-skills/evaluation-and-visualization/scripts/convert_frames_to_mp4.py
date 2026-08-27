#!/usr/bin/env python3
"""Convert supported local rPPG dataset layouts to MP4 for OpenFace input."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

import numpy as np


def _read_video(path: Path) -> np.ndarray:
    """Read an OpenCV video and return RGB frames."""
    import cv2

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"cannot open video: {path}")
    frames = []
    try:
        while True:
            success, frame = capture.read()
            if not success:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        capture.release()
    if not frames:
        raise ValueError(f"video has no readable frames: {path}")
    return np.asarray(frames)


def _read_png_frames(directory: Path) -> np.ndarray:
    """Read a deterministically sorted PNG sequence as RGB frames."""
    import cv2

    paths = sorted(directory.rglob("*.png"))
    frames = []
    for path in paths:
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError(f"cannot decode PNG: {path}")
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if not frames:
        raise ValueError(f"no PNG frames found under: {directory}")
    return np.asarray(frames)


def _read_mat_video(path: Path) -> np.ndarray:
    """Read the MMPD ``video`` MATLAB array as RGB frames."""
    from scipy.io import loadmat

    try:
        data = loadmat(path)
    except Exception as error:
        raise ValueError(f"cannot read MATLAB file {path}: {error}") from error
    if "video" not in data:
        raise ValueError(f"MATLAB file has no 'video' array: {path}")
    frames = np.asarray(data["video"])
    if frames.ndim != 4:
        raise ValueError(f"MMPD video must be 4-D, got {frames.shape}: {path}")
    # Most files are T,H,W,C. Handle the common H,W,C,T variant explicitly.
    if frames.shape[-1] in {3, 4}:
        return frames[..., :3]
    if frames.shape[2] in {3, 4}:
        return np.moveaxis(frames[..., :3, :], -1, 0)
    raise ValueError(f"cannot identify RGB channel axis in {frames.shape}: {path}")


def _as_uint8(frames: np.ndarray, source: Path) -> np.ndarray:
    """Validate frame shape and normalize only documented numeric ranges."""
    frames = np.asarray(frames)
    if frames.ndim != 4 or frames.shape[-1] < 3 or frames.shape[0] == 0:
        raise ValueError(f"frames must be nonempty (T,H,W,3+), got {frames.shape}: {source}")
    frames = frames[..., :3]
    if not np.issubdtype(frames.dtype, np.number) or not np.all(np.isfinite(frames)):
        raise ValueError(f"frames contain nonnumeric or nonfinite values: {source}")
    minimum, maximum = float(np.min(frames)), float(np.max(frames))
    if np.issubdtype(frames.dtype, np.integer) and 0 <= minimum and maximum <= 255:
        return frames.astype(np.uint8)
    if np.issubdtype(frames.dtype, np.floating) and 0 <= minimum and maximum <= 1:
        return np.rint(frames * 255).astype(np.uint8)
    raise ValueError(f"frame values must be integer [0,255] or float [0,1], got [{minimum}, {maximum}]: {source}")


def _write_video(frames: np.ndarray, output: Path, fps: float, force: bool, source: Path) -> None:
    """Write RGB frames to one MP4, refusing replacement by default."""
    import cv2

    if output.exists() and not force:
        raise FileExistsError(f"refusing to overwrite {output}; use --force")
    output.parent.mkdir(parents=True, exist_ok=True)
    height, width = frames.shape[1:3]
    if height == 0 or width == 0:
        raise ValueError(f"frame has zero height/width: {source}")
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        raise OSError(f"cannot open MP4 writer: {output}")
    try:
        for frame in frames:
            writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    finally:
        writer.release()
    if not output.is_file() or output.stat().st_size == 0:
        raise OSError(f"MP4 writer produced no output: {output}")
    print(f"saved {output}")


def _jobs(mode: str, root: Path) -> list[tuple[str, Path, Callable[[], np.ndarray]]]:
    """Discover mode-specific inputs without embedding dataset paths."""
    jobs: list[tuple[str, Path, Callable[[], np.ndarray]]] = []
    if mode == "ubfc-rppg":
        for directory in sorted(root.glob("subject*")):
            source = directory / "vid.avi"
            if source.is_file():
                jobs.append((directory.name, source, lambda source=source: _read_video(source)))
    elif mode == "ubfc-phys":
        for source in sorted(root.glob("s*/*.avi")):
            jobs.append((source.stem, source, lambda source=source: _read_video(source)))
    elif mode == "pure":
        for directory in sorted(path for path in root.glob("*-*") if path.is_dir()):
            jobs.append((directory.name, directory, lambda directory=directory: _read_png_frames(directory)))
    elif mode == "afrl":
        for source in sorted(root.glob("*.avi")):
            jobs.append((source.stem, source, lambda source=source: _read_video(source)))
    elif mode == "mmpd":
        for source in sorted(root.glob("subject*/*.mat")):
            jobs.append((source.stem, source, lambda source=source: _read_mat_video(source)))
    else:  # argparse choices should make this unreachable.
        raise ValueError(f"unsupported mode: {mode}")
    return jobs


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("ubfc-rppg", "ubfc-phys", "pure", "afrl", "mmpd"), help="dataset layout")
    parser.add_argument("--input-dir", required=True, help="local dataset root")
    parser.add_argument("--output-dir", required=True, help="directory for generated MP4 files")
    parser.add_argument("--fps", type=float, default=30.0, help="output frame rate in Hz (default: 30)")
    parser.add_argument("--force", action="store_true", help="allow replacing existing MP4 files")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Discover, convert, and write local dataset videos."""
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        root, output_dir = Path(args.input_dir).expanduser(), Path(args.output_dir).expanduser()
        if not root.is_dir():
            raise ValueError(f"input directory does not exist: {root}")
        if not np.isfinite(args.fps) or args.fps <= 0:
            raise ValueError("fps must be positive")
        jobs = _jobs(args.mode, root)
        if not jobs:
            raise ValueError(f"no inputs found for mode {args.mode!r} under {root}")
        output_names = [name + ".mp4" for name, _, _ in jobs]
        if len(output_names) != len(set(output_names)):
            raise ValueError("discovered inputs produce duplicate output names")
        for name, source, reader in jobs:
            frames = _as_uint8(reader(), source)
            _write_video(frames, output_dir / f"{name}.mp4", args.fps, args.force, source)
        print(f"converted {len(jobs)} dataset item(s)")
        return 0
    except (FileExistsError, OSError, ValueError, ImportError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
