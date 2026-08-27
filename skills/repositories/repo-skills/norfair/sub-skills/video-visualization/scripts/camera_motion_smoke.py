#!/usr/bin/env python3
"""Safe synthetic camera-motion smoke for Norfair visualization.

The script generates a textured scene, simulates camera translation, estimates
motion with ``MotionEstimator``, draws an absolute grid/path, stabilizes with
``FixedCamera``, writes an output video, and re-reads it. It has no detector,
model-download, camera, GPU, Docker, or repository-demo dependency.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AbsoluteTrackObject:
    """Minimal object with the attributes ``AbsolutePaths.draw`` needs."""

    id: int
    absolute_points: Any
    live_points: Any

    def get_estimate(self, absolute: bool = False) -> Any:  # noqa: ARG002 - mirrors Norfair API
        return self.absolute_points


def import_runtime() -> dict[str, Any]:
    """Import runtime dependencies after argparse so ``--help`` is cheap."""
    try:
        import cv2
        import numpy as np
        from norfair import Detection, Video
        from norfair.camera_motion import (
            MotionEstimator,
            TranslationTransformation,
            TranslationTransformationGetter,
        )
        from norfair.drawing import (
            AbsolutePaths,
            Color,
            FixedCamera,
            draw_absolute_grid,
            draw_boxes,
        )
    except ImportError as exc:
        raise SystemExit(
            "Missing runtime dependency for Norfair camera-motion smoke. Install Norfair "
            "with video support, for example `pip install norfair[video]`, and ensure "
            "numpy/OpenCV are importable."
        ) from exc
    return {
        "cv2": cv2,
        "np": np,
        "Detection": Detection,
        "Video": Video,
        "MotionEstimator": MotionEstimator,
        "TranslationTransformation": TranslationTransformation,
        "TranslationTransformationGetter": TranslationTransformationGetter,
        "AbsolutePaths": AbsolutePaths,
        "Color": Color,
        "FixedCamera": FixedCamera,
        "draw_absolute_grid": draw_absolute_grid,
        "draw_boxes": draw_boxes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a synthetic Norfair MotionEstimator + FixedCamera smoke."
    )
    parser.add_argument("--frames", type=int, default=7, help="Synthetic frame count.")
    parser.add_argument("--width", type=int, default=160, help="Source frame width in pixels.")
    parser.add_argument("--height", type=int, default=120, help="Source frame height in pixels.")
    parser.add_argument("--fps", type=float, default=8.0, help="Synthetic video FPS.")
    parser.add_argument("--shift-x", type=float, default=3.0, help="Camera translation per frame in x pixels.")
    parser.add_argument("--shift-y", type=float, default=2.0, help="Camera translation per frame in y pixels.")
    parser.add_argument("--scale", type=float, default=2.4, help="FixedCamera scale for the stabilized canvas.")
    parser.add_argument("--path-history", type=int, default=8, help="AbsolutePaths history length.")
    parser.add_argument(
        "--draw-flow",
        action="store_true",
        help="Draw optical-flow debug lines on the source frame before stabilization.",
    )
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
        help="Extension Norfair should use for the stabilized output video.",
    )
    parser.add_argument(
        "--output-fourcc",
        default=None,
        help="Optional OpenCV fourcc for Norfair's output writer, e.g. mp4v or XVID.",
    )
    args = parser.parse_args()
    if args.frames < 3:
        parser.error("--frames must be at least 3")
    if args.width < 96 or args.height < 96:
        parser.error("--width and --height must both be at least 96")
    if args.fps <= 0:
        parser.error("--fps must be positive")
    if args.scale <= 1.0:
        parser.error("--scale must be greater than 1.0")
    if args.path_history < 1:
        parser.error("--path-history must be positive")
    return args


def make_base_scene(np: Any, cv2: Any, width: int, height: int, box_abs: Any) -> Any:
    """Build a high-corner textured BGR scene for optical flow."""
    tile = max(8, min(width, height) // 10)
    yy, xx = np.indices((height, width))
    checker = (((xx // tile + yy // tile) % 2) * 110 + 50).astype(np.uint8)
    frame = np.dstack(
        [
            checker,
            np.roll(checker, tile // 2, axis=1),
            np.full_like(checker, 35, dtype=np.uint8),
        ]
    )
    for y in range(tile // 2, height, tile):
        cv2.line(frame, (0, y), (width - 1, y), (25, 25, 25), 1)
    for x in range(tile // 2, width, tile):
        cv2.line(frame, (x, 0), (x, height - 1), (25, 25, 25), 1)
    p0, p1 = box_abs.astype(int)
    cv2.rectangle(frame, tuple(p0), tuple(p1), (40, 220, 60), -1)
    cv2.rectangle(frame, tuple(p0), tuple(p1), (0, 80, 0), 2)
    return frame


def translate_frame(cv2: Any, np: Any, frame: Any, shift: tuple[float, float]) -> Any:
    height, width = frame.shape[:2]
    matrix = np.float32([[1, 0, shift[0]], [0, 1, shift[1]]])
    return cv2.warpAffine(
        frame,
        matrix,
        (width, height),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0),
    )


def mask_out_box(np: Any, frame_shape: tuple[int, int, int], box_abs: Any, shift: tuple[float, float]) -> Any:
    height, width = frame_shape[:2]
    mask = np.ones((height, width), dtype=np.uint8)
    shifted = box_abs + np.array(shift, dtype=float)
    x0, y0 = np.floor(shifted[0]).astype(int)
    x1, y1 = np.ceil(shifted[1]).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, width), min(y1, height)
    if x0 < x1 and y0 < y1:
        mask[y0:y1, x0:x1] = 0
    return mask


def create_source_video(cv2: Any, frames: list[Any], output_dir: Path, fps: float) -> tuple[Path, str]:
    height, width = frames[0].shape[:2]
    candidates = [("source_camera_motion.mp4", "mp4v"), ("source_camera_motion.avi", "XVID")]
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
    raise RuntimeError("Could not create a readable synthetic motion source video with mp4v or XVID")


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
    MotionEstimator = runtime["MotionEstimator"]
    TranslationTransformation = runtime["TranslationTransformation"]
    TranslationTransformationGetter = runtime["TranslationTransformationGetter"]
    AbsolutePaths = runtime["AbsolutePaths"]
    Color = runtime["Color"]
    FixedCamera = runtime["FixedCamera"]
    draw_absolute_grid = runtime["draw_absolute_grid"]
    draw_boxes = runtime["draw_boxes"]

    output_dir.mkdir(parents=True, exist_ok=True)
    box_abs = np.array(
        [
            [args.width * 0.42, args.height * 0.38],
            [args.width * 0.58, args.height * 0.62],
        ],
        dtype=float,
    )
    base_scene = make_base_scene(np, cv2, args.width, args.height, box_abs)
    shifts = [(idx * args.shift_x, idx * args.shift_y) for idx in range(args.frames)]
    source_frames = [translate_frame(cv2, np, base_scene, shift) for shift in shifts]
    input_path, input_fourcc = create_source_video(cv2, source_frames, output_dir, args.fps)
    input_count, _ = count_video_frames(cv2, input_path)
    if input_count != args.frames:
        raise AssertionError(f"Expected {args.frames} source frames, found {input_count}")

    motion_estimator = MotionEstimator(
        max_points=250,
        min_distance=7,
        transformations_getter=TranslationTransformationGetter(),
        draw_flow=args.draw_flow,
        quality_level=0.01,
    )
    current_transform = TranslationTransformation(np.zeros(2, dtype=float))
    fixed_camera = FixedCamera(scale=args.scale)
    absolute_paths = AbsolutePaths(
        get_points_to_draw=lambda points: np.mean(np.asarray(points), axis=0, keepdims=True),
        max_history=args.path_history,
        thickness=2,
        radius=2,
        color=Color.yellow,
    )
    track = AbsoluteTrackObject(
        id=1,
        absolute_points=box_abs,
        live_points=np.array([True, True], dtype=bool),
    )

    video = Video(
        input_path=str(input_path),
        output_path=str(output_dir),
        output_fourcc=args.output_fourcc,
        output_extension=args.output_extension,
        label="camera motion smoke",
    )
    output_path = Path(video.get_output_file_path())
    if output_path.exists():
        output_path.unlink()

    vectors: list[list[float]] = []
    non_none_transforms = 0
    written = 0
    for index, frame in enumerate(video):
        mask = mask_out_box(np, frame.shape, box_abs, shifts[index])
        estimated = motion_estimator.update(frame, mask=mask)
        if estimated is not None:
            current_transform = estimated
            non_none_transforms += 1
        if hasattr(current_transform, "movement_vector"):
            vectors.append([float(v) for v in np.asarray(current_transform.movement_vector).ravel()])

        relative_box = current_transform.abs_to_rel(box_abs)
        overlay_detection = Detection(points=relative_box, label="absolute-box")
        draw_boxes(frame, [overlay_detection], color=Color.orange, draw_labels=True, draw_ids=False)
        draw_absolute_grid(frame, current_transform, grid_size=10, radius=1, thickness=1, color=Color.cyan)
        frame = absolute_paths.draw(frame, [track], coord_transform=current_transform)
        stabilized = fixed_camera.adjust_frame(frame, current_transform)
        if stabilized.shape[0] <= frame.shape[0] or stabilized.shape[1] <= frame.shape[1]:
            raise AssertionError("FixedCamera did not create a larger stabilized canvas")
        video.write(stabilized)
        writer = getattr(video, "output_video", None)
        if writer is not None and hasattr(writer, "isOpened") and not writer.isOpened():
            raise RuntimeError(f"OpenCV VideoWriter failed to open {output_path}")
        written += 1

    output_count, output_checksums = count_video_frames(cv2, output_path)
    if written != args.frames:
        raise AssertionError(f"Expected to process {args.frames} frames, processed {written}")
    if output_count != written:
        raise AssertionError(f"Expected {written} stabilized output frames, found {output_count}")
    if non_none_transforms < args.frames - 1:
        raise AssertionError(
            f"Expected motion estimates for most frames, got {non_none_transforms}/{args.frames}"
        )
    if not output_checksums or max(output_checksums) <= 0:
        raise AssertionError("Stabilized output video appears empty")

    return {
        "status": "ok",
        "kept_outputs": keep_outputs,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "frames": written,
        "input_fourcc": input_fourcc,
        "output_extension": args.output_extension,
        "non_none_transforms": non_none_transforms,
        "last_movement_vector": vectors[-1] if vectors else None,
        "scale": args.scale,
    }


def main() -> None:
    args = parse_args()
    if args.output_dir is not None:
        summary = run_smoke(args, args.output_dir.expanduser(), keep_outputs=True)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    with tempfile.TemporaryDirectory(prefix="norfair-camera-motion-smoke-") as tmp:
        summary = run_smoke(args, Path(tmp), keep_outputs=False)
        print(json.dumps(summary, indent=2, sort_keys=True))
        print("Temporary smoke videos were removed. Pass --output-dir to keep them.")


if __name__ == "__main__":
    main()
