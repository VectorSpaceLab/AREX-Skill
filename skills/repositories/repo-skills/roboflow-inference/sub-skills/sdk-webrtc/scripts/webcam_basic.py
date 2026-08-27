#!/usr/bin/env python3
"""Interactive webcam example for the Inference SDK WebRTC surface.

Safe modes:
- `--help` prints the parser without importing the runtime surface.
- `--dry-run` prints the planned session without opening a camera or network.

Example:
    python scripts/webcam_basic.py --workspace-name my-workspace                 --workflow-id my-workflow --api-url http://localhost:9001
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
        prog="webcam_basic.py",
        description="Stream webcam frames through the Inference SDK WebRTC client.",
    )
    parser.add_argument("--api-url", default="https://serverless.roboflow.com")
    parser.add_argument("--api-key", default=None)
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional local checkout root to add to PYTHONPATH before import.",
    )
    parser.add_argument("--image-input-name", default="image")
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--stream-output", default=None)
    parser.add_argument("--data-output", default=None)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--dry-run", action="store_true")

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--workflow-id", default=None)
    mode.add_argument("--model-id", default=None)

    parser.add_argument("--workspace-name", default=None)
    parser.add_argument("--task-type", choices=SUPPORTED_TASK_TYPES, default=None)
    return parser


def _build_plan(args: argparse.Namespace) -> Dict[str, Any]:
    resolution = None
    if args.width is not None and args.height is not None:
        resolution = [args.width, args.height]

    plan: Dict[str, Any] = {
        "api_url": args.api_url,
        "source": {
            "type": "WebcamSource",
            "device_id": 0,
            "resolution": resolution,
        },
        "outputs": {
            "stream_output": _parse_csv(args.stream_output),
            "data_output": _parse_csv(args.data_output),
        },
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
    from inference_sdk.webrtc import StreamConfig, VideoMetadata, WebcamSource
    return InferenceHTTPClient, StreamConfig, VideoMetadata, WebcamSource


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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.workflow_id and not args.workspace_name:
        parser.error("--workspace-name is required when using --workflow-id")

    if args.dry_run:
        print(pformat(_build_plan(args), sort_dicts=False))
        return 0

    try:
        InferenceHTTPClient, StreamConfig, VideoMetadata, WebcamSource = _load_runtime_surface(args.repo_root)
    except (ImportError, ModuleNotFoundError) as exc:
        return _print_import_hint(exc)

    try:
        import cv2
    except (ImportError, ModuleNotFoundError) as exc:
        return _print_import_hint(exc)

    client = InferenceHTTPClient.init(api_url=args.api_url, api_key=args.api_key)
    resolution = None
    if args.width is not None and args.height is not None:
        resolution = (args.width, args.height)
    source = WebcamSource(resolution=resolution)
    config = StreamConfig(
        stream_output=_parse_csv(args.stream_output),
        data_output=_parse_csv(args.data_output),
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

    if args.model_id:
        @session.on_frame
        def show_frame(frame, data):
            if not args.headless:
                cv2.imshow("WebRTC SDK - Webcam", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    session.close()
    else:
        @session.on_frame
        def show_frame(frame, metadata):
            if not args.headless:
                cv2.imshow("WebRTC SDK - Webcam", frame)
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

    session.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
