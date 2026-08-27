#!/usr/bin/env python3
"""Safe synthetic video round-trip and overlay smoke for Norfair.

The script creates a tiny local video, reads it through ``norfair.Video``,
draws point/box overlays and a relative path, writes an output video, and
re-reads the output to assert that frames were produced. It never downloads
models, opens a GUI window, requires a camera, or reads repository demo files.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RelativePathObject:
    """Minimal object with the attributes ``Paths.draw`` uses."""

    id: int
    estimate: Any
    live_points: Any
    abs_to_rel: Any = None


def import_runtime() -> dict[str, Any]:
    """Import runtime dependencies after argparse so ``--help`` is cheap."""
    try:
        import cv2
        import numpy as np
        from norfair import Detection, Video
        from norfair.drawing import (
            Color,
            Palette,
            Paths,
            draw_boxes,
            draw_points,
            draw_tracked_boxes,
            draw_tracked_objects,
        )
    except ImportError as exc:
        raise SystemExit(
            "Missing runtime dependency for Norfair video smoke. Install Norfair "
            "with video support, for example `pip install norfair[video]`, and "
            "ensure numpy/OpenCV are importable in this Python environment."
        ) from exc
    return {
        "cv2": cv2,
        "np": np,
        "Detection": Detection,
        "Video": Video,
        "Color": Color,
        "Palette": Palette,
        "Paths": Paths,
        "draw_boxes": draw_boxes,
        "draw_points": draw_points,
        "draw_tracked_boxes": draw_tracked_boxes,
        "draw_tracked_objects": draw_tracked_objects,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny Norfair Video round-trip with synthetic overlays."
    )
    parser.add_argument("--frames", type=int, default=6, help="Synthetic frame count.")
    parser.add_argument("--width", type=int, default=128, help="Frame width in pixels.")
    parser.add_argument("--height", type=int, default=96, help="Frame height in pixels.")
    parser.add_argument("--fps", type=float, default=8.0, help="Synthetic video FPS.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where input/output smoke videos are kept. If omitted, a temporary directory is cleaned up.",
    )
    parser.add_argument(
        "--output-extension",
        choices=["mp4", "avi"],
        default="mp4",
        help="Extension Norfair should use for the output video when output-dir is a folder.",
    )
    parser.add_argument(
        "--output-fourcc",
        default=None,
        help="Optional OpenCV fourcc for Norfair's output writer, e.g. mp4v or XVID.",
    )
    parser.add_argument(
        "--exercise-deprecated-aliases",
        action="store_true",
        help="Also call legacy draw_tracked_objects/draw_tracked_boxes wrappers; they may emit deprecation warnings.",
    )
    args = parser.parse_args()
    if args.frames < 2:
        parser.error("--frames must be at least 2")
    if args.width < 64 or args.height < 64:
        parser.error("--width and --height must both be at least 64")
    if args.fps <= 0:
        parser.error("--fps must be positive")
    return args


def make_frame(np: Any, cv2: Any, width: int, height: int, index: int, total: int) -> Any:
    """Create a deterministic BGR frame with a moving shape."""
    x_gradient = np.arange(width, dtype=np.uint8)[None, :]
    y_gradient = np.arange(height, dtype=np.uint8)[:, None]
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, :, 0] = (x_gradient + index * 11) % 255
    frame[:, :, 1] = (2 * y_gradient + 30) % 255
    frame[:, :, 2] = 45

    cx = 20 + int((width - 40) * index / max(total - 1, 1))
    cy = height // 2
    cv2.circle(frame, (cx, cy), 6, (30, 220, 220), -1)
    cv2.rectangle(frame, (cx - 12, cy - 10), (cx + 12, cy + 10), (80, 80, 210), 1)
    return frame


def make_detections(np: Any, Detection: Any, width: int, height: int, index: int, total: int) -> tuple[Any, Any, Any]:
    cx = 20 + int((width - 40) * index / max(total - 1, 1))
    cy = height // 2
    point = np.array([[cx, cy]], dtype=float)
    box = np.array([[cx - 12, cy - 10], [cx + 12, cy + 10]], dtype=float)
    point_detection = Detection(points=point, scores=np.array([0.92]), label="centroid")
    box_detection = Detection(points=box, scores=np.array([0.88, 0.88]), label="box")
    path_object = RelativePathObject(
        id=1,
        estimate=point,
        live_points=np.array([True], dtype=bool),
    )
    return point_detection, box_detection, path_object


def create_source_video(cv2: Any, frames: list[Any], output_dir: Path, fps: float) -> tuple[Path, str]:
    """Write a readable source video, trying common container/codecs."""
    height, width = frames[0].shape[:2]
    candidates = [("source_video_smoke.mp4", "mp4v"), ("source_video_smoke.avi", "XVID")]
    for filename, fourcc_name in candidates:
        path = output_dir / filename
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*fourcc_name), fps, (width, height))
        if not writer.isOpened():
            writer.release()
            continue
        for frame in frames:
            writer.write(frame)
        writer.release()
        count, _ = count_video_frames(cv2, path)
        if count == len(frames):
            return path, fourcc_name
    raise RuntimeError("Could not create a readable synthetic source video with mp4v or XVID")


def count_video_frames(cv2: Any, path: Path) -> tuple[int, list[int]]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return 0, []
    count = 0
    checksums: list[int] = []
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        count += 1
        checksums.append(int(frame.sum()))
    cap.release()
    return count, checksums


def run_smoke(args: argparse.Namespace, output_dir: Path, keep_outputs: bool) -> dict[str, Any]:
    runtime = import_runtime()
    cv2 = runtime["cv2"]
    np = runtime["np"]
    Detection = runtime["Detection"]
    Video = runtime["Video"]
    Color = runtime["Color"]
    Palette = runtime["Palette"]
    Paths = runtime["Paths"]
    draw_boxes = runtime["draw_boxes"]
    draw_points = runtime["draw_points"]
    draw_tracked_boxes = runtime["draw_tracked_boxes"]
    draw_tracked_objects = runtime["draw_tracked_objects"]

    output_dir.mkdir(parents=True, exist_ok=True)
    Palette.set("colorblind")

    source_frames = [
        make_frame(np, cv2, args.width, args.height, idx, args.frames)
        for idx in range(args.frames)
    ]
    input_path, input_fourcc = create_source_video(cv2, source_frames, output_dir, args.fps)
    input_count, input_checksums = count_video_frames(cv2, input_path)
    if input_count != args.frames:
        raise AssertionError(f"Expected {args.frames} input frames, found {input_count}")

    video = Video(
        input_path=str(input_path),
        output_path=str(output_dir),
        output_fourcc=args.output_fourcc,
        output_extension=args.output_extension,
        label="video smoke",
    )
    output_path = Path(video.get_output_file_path())
    if output_path.exists():
        output_path.unlink()

    path_drawer = Paths(
        get_points_to_draw=lambda points: np.mean(np.asarray(points), axis=0, keepdims=True),
        attenuation=0.0,
        radius=2,
        thickness=2,
        color=Color.yellow,
    )

    written = 0
    for index, frame in enumerate(video):
        point_detection, box_detection, path_object = make_detections(
            np, Detection, args.width, args.height, index, args.frames
        )
        draw_points(
            frame,
            [point_detection],
            color="by_label",
            draw_labels=True,
            draw_scores=True,
            draw_ids=False,
            text_color=Color.white,
        )
        draw_boxes(
            frame,
            [box_detection],
            color=Color.orange,
            draw_labels=True,
            draw_scores=True,
            draw_ids=False,
        )
        if args.exercise_deprecated_aliases:
            draw_tracked_objects(frame, [point_detection], draw_labels=True)
            draw_tracked_boxes(frame, [box_detection], draw_labels=True)
        frame = path_drawer.draw(frame, [path_object])
        video.write(frame)
        writer = getattr(video, "output_video", None)
        if writer is not None and hasattr(writer, "isOpened") and not writer.isOpened():
            raise RuntimeError(f"OpenCV VideoWriter failed to open {output_path}")
        written += 1

    output_count, output_checksums = count_video_frames(cv2, output_path)
    if output_count != written:
        raise AssertionError(f"Expected {written} output frames, found {output_count}")
    if written != args.frames:
        raise AssertionError(f"Expected to process {args.frames} frames, processed {written}")
    if not output_checksums or output_checksums == input_checksums[: len(output_checksums)]:
        raise AssertionError("Output video checksums did not change after overlays")

    return {
        "status": "ok",
        "kept_outputs": keep_outputs,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "frames": written,
        "input_fourcc": input_fourcc,
        "output_extension": args.output_extension,
        "overlay_checksum_delta": int(sum(output_checksums) - sum(input_checksums[: len(output_checksums)])),
    }


def main() -> None:
    args = parse_args()
    if args.output_dir is not None:
        summary = run_smoke(args, args.output_dir.expanduser(), keep_outputs=True)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    with tempfile.TemporaryDirectory(prefix="norfair-video-smoke-") as tmp:
        summary = run_smoke(args, Path(tmp), keep_outputs=False)
        print(json.dumps(summary, indent=2, sort_keys=True))
        print("Temporary smoke videos were removed. Pass --output-dir to keep them.")


if __name__ == "__main__":
    main()
