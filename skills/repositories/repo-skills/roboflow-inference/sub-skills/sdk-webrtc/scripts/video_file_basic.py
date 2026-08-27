#!/usr/bin/env python3
"""Interactive video-file example for the Inference SDK WebRTC surface.

Safe modes:
- `--help` prints the parser without importing the runtime surface.
- `--dry-run` prints the planned session without opening the video or server.

Example:
    python scripts/video_file_basic.py --video-path ./clip.mp4                 --workspace-name my-workspace --workflow-id my-workflow
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, Optional


SUPPORTED_TASK_TYPES = [
    "object-detection",
    "instance-segmentation",
    "classification",
    "multi-label-classification",
    "keypoint-detection",
    "semantic-segmentation",
]


def _parse_csv(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _maybe_add_repo_root(repo_root: Optional[str]) -> None:
    if not repo_root:
        return
    root = str(Path(repo_root).expanduser().resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="video_file_basic.py",
        description="Stream a video file through the Inference SDK WebRTC client.",
    )
    parser.add_argument("--video-path", required=True)
    parser.add_argument("--api-url", default="https://serverless.roboflow.com")
    parser.add_argument("--api-key", default=None)
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional local checkout root to add to PYTHONPATH before import.",
    )
    parser.add_argument("--image-input-name", default="image")
    parser.add_argument("--stream-output", default=None)
    parser.add_argument("--data-output", default=None)
    parser.add_argument("--file-output", default=None)
    parser.add_argument("--realtime-processing", action="store_true")
    parser.add_argument("--use-cache", dest="use_cache", action="store_true")
    parser.add_argument("--no-cache", dest="use_cache", action="store_false")
    parser.add_argument("--use-datachannel-frames", dest="use_datachannel_frames", action="store_true")
    parser.add_argument("--no-datachannel-frames", dest="use_datachannel_frames", action="store_false")
    parser.set_defaults(use_cache=True, use_datachannel_frames=True)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--workflow-id", default=None)
    mode.add_argument("--model-id", default=None)

    parser.add_argument("--workspace-name", default=None)
    parser.add_argument("--task-type", choices=SUPPORTED_TASK_TYPES, default=None)
    return parser


def _build_plan(args: argparse.Namespace) -> Dict[str, Any]:
    plan: Dict[str, Any] = {
        "api_url": args.api_url,
        "source": {
            "type": "VideoFileSource",
            "path": args.video_path,
            "use_datachannel_frames": bool(args.use_datachannel_frames),
            "realtime_processing": bool(args.realtime_processing),
            "use_cache": bool(args.use_cache),
        },
        "outputs": {
            "stream_output": _parse_csv(args.stream_output),
            "data_output": _parse_csv(args.data_output),
        },
        "file_output": args.file_output,
        "ui": {"headless": bool(args.headless)},
    }
    if args.model_id:
        plan["mode"] = "model_id"
        plan["model_id"] = args.model_id
        plan["task_type"] = args.task_type
    else:
        plan["mode"] = "workflow"
        plan["workflow_id"] = args.workflow_id
        plan["workspace_name"] = args.workspace_name
    return plan


def _load_runtime_surface(repo_root: Optional[str] = None):
    _maybe_add_repo_root(repo_root)
    from inference_sdk import InferenceHTTPClient
    from inference_sdk.webrtc import StreamConfig, VideoFileSource, VideoMetadata
    return InferenceHTTPClient, StreamConfig, VideoFileSource, VideoMetadata


def _print_import_hint(exc: BaseException) -> int:
    message = str(exc)
    print(f"Could not import the SDK runtime surface: {message}")
    print(
        "If the message mentions `dataclasses_json`, install the base SDK. "
        "If it mentions `aiortc` or `av`, install `inference-sdk[webrtc]`."
    )
    print(
        "If it mentions `cv2`, install `opencv-python` or `opencv-python-headless`."
    )
    return 2


def _get_video_fps(video_path: str) -> float:
    if not Path(video_path).is_file():
        return 30.0
    cap = cv2.VideoCapture(video_path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        return fps if fps and fps > 0 else 30.0
    finally:
        cap.release()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.workflow_id and not args.workspace_name:
        parser.error("--workspace-name is required when using --workflow-id")

    if args.dry_run:
        print(pformat(_build_plan(args), sort_dicts=False))
        return 0

    try:
        InferenceHTTPClient, StreamConfig, VideoFileSource, VideoMetadata = _load_runtime_surface(args.repo_root)
    except (ImportError, ModuleNotFoundError) as exc:
        return _print_import_hint(exc)

    try:
        import cv2
    except (ImportError, ModuleNotFoundError) as exc:
        return _print_import_hint(exc)

    client = InferenceHTTPClient.init(api_url=args.api_url, api_key=args.api_key)
    source = VideoFileSource(
        args.video_path,
        on_upload_progress=lambda uploaded, total: print(
            f"Upload progress: {uploaded} / {total}"
        ),
        use_datachannel_frames=args.use_datachannel_frames,
        realtime_processing=args.realtime_processing,
        use_cache=args.use_cache,
    )
    config = StreamConfig(
        stream_output=_parse_csv(args.stream_output),
        data_output=_parse_csv(args.data_output),
        realtime_processing=args.realtime_processing,
    )

    if args.model_id:
        session = client.webrtc.stream(
            source=source,
            model_id=args.model_id,
            task_type=args.task_type,
            image_input=args.image_input_name,
            config=config,
        )
    else:
        session = client.webrtc.stream(
            source=source,
            workflow=args.workflow_id,
            workspace=args.workspace_name,
            image_input=args.image_input_name,
            config=config,
        )

    writer = None
    fps = _get_video_fps(args.video_path) if args.file_output else None

    if args.model_id:
        @session.on_frame
        def show_frame(frame, data):
            nonlocal writer
            if args.file_output and writer is None:
                h, w = frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(args.file_output, fourcc, fps or 30.0, (w, h))
            if writer is not None:
                writer.write(frame)
            if not args.headless:
                cv2.imshow("WebRTC SDK - Video File", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    session.close()
    else:
        @session.on_frame
        def show_frame(frame, metadata):
            nonlocal writer
            if args.file_output and writer is None:
                h, w = frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(args.file_output, fourcc, fps or 30.0, (w, h))
            if writer is not None:
                writer.write(frame)
            if not args.headless:
                cv2.imshow("WebRTC SDK - Video File", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    session.close()

    @session.on_data()
    def on_message(data: dict, metadata: Optional[VideoMetadata] = None):
        if metadata is None:
            print(data)
        else:
            print(f"Frame {metadata.frame_id}: {data}")

    @session.on_error
    def on_frame_error(errors, metadata: Optional[VideoMetadata] = None):
        frame_id = metadata.frame_id if metadata is not None else "?"
        print(f"Frame {frame_id} errors: {errors}")

    try:
        session.run()
    finally:
        if writer is not None:
            writer.release()
        if args.file_output:
            print(f"Saved output to {args.file_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
