#!/usr/bin/env python3
"""Submit a LightX2V video task in sync or async mode."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Any

import requests


def _maybe_encode_local_file(value: str) -> str:
    if not value:
        return value
    path = Path(value)
    if path.is_file():
        return base64.b64encode(path.read_bytes()).decode("utf-8")
    return value


def _build_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "prompt": args.prompt,
        "negative_prompt": args.negative_prompt,
        "infer_steps": args.infer_steps,
        "seed": args.seed,
        "save_result_path": args.save_result_path,
        "use_prompt_enhancer": args.use_prompt_enhancer,
        "num_fragments": args.num_fragments,
        "target_video_length": args.target_video_length,
        "video_duration": args.video_duration,
        "target_fps": args.target_fps,
        "resize_mode": args.resize_mode,
    }
    if args.target_shape:
        payload["target_shape"] = args.target_shape

    image_path = _maybe_encode_local_file(args.image_path)
    if image_path:
        payload["image_path"] = image_path

    last_frame_path = _maybe_encode_local_file(args.last_frame_path)
    if last_frame_path:
        payload["last_frame_path"] = last_frame_path

    audio_path = _maybe_encode_local_file(args.audio_path)
    if audio_path:
        payload["audio_path"] = audio_path

    video_path = _maybe_encode_local_file(args.video_path)
    if video_path:
        payload["video_path"] = video_path

    return payload


def _save_bytes(data: bytes, output: str) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _submit_async(base_url: str, payload: dict[str, Any]) -> str:
    response = requests.post(f"{base_url.rstrip('/')}/v1/tasks/video/", json=payload, timeout=30)
    response.raise_for_status()
    task_id = response.json().get("task_id")
    if not task_id:
        raise RuntimeError(f"Task submission succeeded but did not return task_id: {response.text}")
    return str(task_id)


def _poll_and_download(base_url: str, task_id: str, timeout_seconds: int, poll_interval: float, output: str) -> Path:
    import time

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        status = requests.get(f"{base_url.rstrip('/')}/v1/tasks/{task_id}/status", timeout=30)
        status.raise_for_status()
        data = status.json()
        task_status = data.get("status")
        print(f"[poll] task_id={task_id} status={task_status}")
        if task_status == "completed":
            result = requests.get(f"{base_url.rstrip('/')}/v1/tasks/{task_id}/result", timeout=120)
            result.raise_for_status()
            return _save_bytes(result.content, output)
        if task_status in {"failed", "cancelled"}:
            raise RuntimeError(f"Task {task_id} ended with status={task_status}: {data.get('error')}")
        time.sleep(poll_interval)
    raise TimeoutError(f"Task {task_id} timed out after {timeout_seconds}s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit a LightX2V video task")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base server URL")
    parser.add_argument("--mode", choices=["sync", "async"], default="sync", help="Request mode")
    parser.add_argument("--prompt", required=True, help="Prompt text")
    parser.add_argument("--negative-prompt", default="", help="Negative prompt text")
    parser.add_argument("--infer-steps", type=int, default=50, help="Inference steps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--save-result-path", default="", help="Server-side save_result_path")
    parser.add_argument("--use-prompt-enhancer", action="store_true", help="Enable prompt enhancement")
    parser.add_argument("--num-fragments", type=int, default=1, help="Number of fragments")
    parser.add_argument("--target-video-length", type=int, default=81, help="Target video length")
    parser.add_argument("--video-duration", type=int, default=5, help="Video duration for audio-driven tasks")
    parser.add_argument("--target-fps", type=int, default=16, help="Target FPS")
    parser.add_argument("--resize-mode", default="adaptive", help="Resize mode")
    parser.add_argument("--target-shape", type=int, nargs=2, default=None, metavar=("HEIGHT", "WIDTH"), help="Optional target shape")
    parser.add_argument("--image-path", default="", help="Local file path, base64 payload, or URL")
    parser.add_argument("--last-frame-path", default="", help="Local file path, base64 payload, or URL")
    parser.add_argument("--audio-path", default="", help="Local file path, base64 payload, or URL")
    parser.add_argument("--video-path", default="", help="Local file path, base64 payload, or URL")
    parser.add_argument("--timeout-seconds", type=int, default=1200, help="Sync or polling timeout")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Polling interval for async mode")
    parser.add_argument("--output", default="save_results/video_task.mp4", help="Local output path for the result")
    args = parser.parse_args()

    payload = _build_payload(args)
    base = args.url.rstrip("/")

    if args.mode == "sync":
        endpoint = f"{base}/v1/tasks/video/"
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        body = response.json()
        print(json.dumps(body, ensure_ascii=False, indent=2, default=str))
        return 0

    task_id = _submit_async(base, payload)
    print(f"Task submitted: {task_id}")
    path = _poll_and_download(base, task_id, args.timeout_seconds, args.poll_interval, args.output)
    print(f"Saved video to: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
