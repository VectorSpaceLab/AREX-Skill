#!/usr/bin/env python3
"""Extract camera and video-model frames from AlpaSim ASL logs."""

from __future__ import annotations

import argparse
import asyncio
import glob
import logging
from dataclasses import dataclass
from typing import Literal, TypeAlias

import aiofiles
import numpy as np
from aiofiles import os as aios
from alpasim_grpc.v0.egodriver_pb2 import DriveSessionRequest, RolloutCameraImage
from alpasim_grpc.v0.logging_pb2 import RolloutMetadata
from alpasim_grpc.v0.video_model_pb2 import VideoChunkRequest, VideoChunkReturn
from alpasim_utils.logs import async_read_pb_log

logger = logging.getLogger("asl_to_frames")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

SaveFormat: TypeAlias = Literal["mp4", "frames"]


@dataclass(frozen=True)
class Frame:
    image_bytes: bytes
    timestamp_us: int


def _imageio():
    try:
        import imageio.v3 as iio
    except ImportError as exc:
        raise RuntimeError(
            "MP4 output requires imageio[ffmpeg]; use --format frames "
            "for codec-free extraction."
        ) from exc
    return iio


def pad_to_divisible_by_16(image: np.ndarray) -> np.ndarray:
    """Pad an HxWx3 image symmetrically to dimensions divisible by 16."""
    if image.ndim != 3 or image.shape[2] not in (1, 3, 4):
        raise ValueError(f"expected an image shaped HxWxC, got {image.shape}")
    h, w, _ = image.shape
    pad_h = (16 - h % 16) % 16
    pad_w = (16 - w % 16) % 16
    return np.pad(
        image,
        (
            (pad_h // 2, pad_h - pad_h // 2),
            (pad_w // 2, pad_w - pad_w // 2),
            (0, 0),
        ),
        mode="constant",
        constant_values=0,
    )


async def convert_single_log(log_path: str, save_dir: str, format: SaveFormat) -> None:
    frames_by_camera: dict[str, list[Frame]] = {}
    video_model_frames: dict[str, list[Frame]] = {}
    pending_chunk: VideoChunkRequest | None = None
    rollout_metadata: RolloutMetadata | None = None
    drive_session: DriveSessionRequest | None = None

    async for message in async_read_pb_log(log_path):
        kind = message.WhichOneof("log_entry")
        if kind == "driver_session_request":
            drive_session = message.driver_session_request
        elif kind == "rollout_metadata":
            rollout_metadata = message.rollout_metadata
        elif kind == "driver_camera_image":
            image: RolloutCameraImage.CameraImage = message.driver_camera_image.camera_image
            frames_by_camera.setdefault(image.logical_id, []).append(
                Frame(image.image_bytes, image.frame_end_us)
            )
        elif kind == "video_model_chunk_request":
            pending_chunk = message.video_model_chunk_request
        elif kind == "video_model_chunk_return":
            if pending_chunk is None:
                logger.warning("Skipping video_model_chunk_return without a request")
            else:
                _collect_video_model_frames(
                    message.video_model_chunk_return, pending_chunk, video_model_frames
                )
                pending_chunk = None

    if rollout_metadata is None:
        raise ValueError("RolloutMetadata not found; cannot identify this rollout")
    if drive_session is None:
        raise ValueError("DriveSessionRequest not found; camera metadata is incomplete")

    await aios.makedirs(save_dir, exist_ok=True)
    await _save_frame_groups(frames_by_camera, save_dir, format)
    await _save_frame_groups(video_model_frames, save_dir, format)


def _collect_video_model_frames(
    response: VideoChunkReturn,
    request: VideoChunkRequest,
    frames_by_name: dict[str, list[Frame]],
) -> None:
    timestamps = [pose.timestamp_us for pose in request.rig_trajectory.poses]
    for camera in response.camera_outputs:
        _extend_frame_group(
            frames_by_name,
            f"video_model_rgb_{camera.camera_logical_id}",
            [image.data for image in camera.rgb_frames],
            timestamps,
        )
        _extend_frame_group(
            frames_by_name,
            f"video_model_hdmap_{camera.camera_logical_id}",
            [image.data for image in camera.hdmap_condition_frames],
            timestamps,
        )


def _extend_frame_group(
    groups: dict[str, list[Frame]],
    name: str,
    image_bytes: list[bytes],
    timestamps: list[int],
) -> None:
    if len(image_bytes) > len(timestamps):
        logger.warning("Dropping %d %s frame(s) without timestamps", len(image_bytes) - len(timestamps), name)
    if not image_bytes or not timestamps:
        return
    groups.setdefault(name, []).extend(
        Frame(data, timestamp)
        for data, timestamp in zip(image_bytes, timestamps)
    )


async def _save_frame_groups(
    groups: dict[str, list[Frame]], save_dir: str, format: SaveFormat
) -> None:
    for name, images in groups.items():
        images = sorted(images, key=lambda item: item.timestamp_us)
        if not images:
            continue
        timestamps = np.asarray([item.timestamp_us for item in images], dtype=np.uint64)
        path = f"{save_dir}/{name}"
        if format == "mp4":
            await frames_to_mp4(images, timestamps, path)
        else:
            await save_frames_as_files(images, timestamps, path)


async def frames_to_mp4(
    images: list[Frame], timestamps_us: np.ndarray, save_path: str
) -> None:
    if not images:
        return
    iio = _imageio()
    if len(images) == 1:
        fps = 1.0
    else:
        deltas = np.diff(timestamps_us.astype(np.float64))
        positive = deltas[deltas > 0]
        if len(positive) == 0:
            raise ValueError("MP4 output needs at least two distinct frame timestamps")
        fps = float(1 / (positive.mean() / 1e6))
    bitmaps = [pad_to_divisible_by_16(iio.imread(item.image_bytes)) for item in images]
    duration_s = (int(timestamps_us[-1]) - int(timestamps_us[0])) / 1e6
    output = f"{save_path}.mp4"
    logger.info("Saving %s (%.2fs, %.2ffps)", output, duration_s, fps)
    iio.imwrite(output, image=bitmaps, extension=".mp4", fps=fps)


async def _write_image(content: bytes, path: str) -> None:
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        suffix = "png"
    elif content[:3] == b"\xff\xd8\xff":
        suffix = "jpg"
    else:
        raise ValueError("frame is neither PNG nor JPEG")
    async with aiofiles.open(f"{path}.{suffix}", "wb") as file:
        await file.write(content)


async def save_frames_as_files(
    images: list[Frame], timestamps_us: np.ndarray, save_path: str
) -> None:
    await aios.makedirs(save_path, exist_ok=True)
    await asyncio.gather(
        *[
            _write_image(item.image_bytes, f"{save_path}/{int(timestamp)}")
            for item, timestamp in zip(images, timestamps_us)
        ]
    )


def determine_save_dir(log_path: str, log_save_dir: str | None) -> str:
    if log_save_dir is None:
        return f"{log_path.removesuffix('.asl')}_asl_frames"
    relative = "/".join(log_path.removesuffix(".asl").split("/")[-3:])
    return f"{log_save_dir}/{relative}"


async def convert_multiple_logs(
    asl_glob: str,
    format: SaveFormat,
    log_save_dir: str | None,
    max_files: int,
    max_concurrency: int,
) -> int:
    if not asl_glob.endswith(".asl"):
        raise ValueError("the glob must end in .asl")
    if max_files <= 0 or max_concurrency <= 0:
        raise ValueError("max-files and max-concurrency must be positive")
    paths = sorted(glob.glob(asl_glob, recursive=True))
    if len(paths) > max_files:
        raise ValueError(f"glob matched {len(paths)} files, exceeding --max-files={max_files}")
    semaphore = asyncio.Semaphore(max_concurrency)

    async def convert(path: str) -> None:
        async with semaphore:
            try:
                await convert_single_log(path, determine_save_dir(path, log_save_dir), format)
            except Exception:
                logger.exception("Skipping %s", path)

    await asyncio.gather(*(convert(path) for path in paths))
    logger.info("Considered %d ASL file(s)", len(paths))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asl_glob", help="Quoted recursive glob ending in .asl")
    parser.add_argument("--format", choices=("mp4", "frames"), default="mp4")
    parser.add_argument("--log-save-dir", default=None, help="Optional output root")
    parser.add_argument("--max-files", type=int, default=1000)
    parser.add_argument("--max-concurrency", type=int, default=4)
    args = parser.parse_args()
    return asyncio.run(
        convert_multiple_logs(
            args.asl_glob,
            args.format,
            args.log_save_dir,
            args.max_files,
            args.max_concurrency,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
