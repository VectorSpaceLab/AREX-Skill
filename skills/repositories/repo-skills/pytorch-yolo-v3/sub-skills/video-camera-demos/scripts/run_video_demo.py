#!/usr/bin/env python3
"""Preflight or launch pytorch-yolo-v3 video/camera demos through a bundled wrapper.

Default mode is dry-run: validate known prerequisites and print the command that
would run a repository demo in a user's checkout. Add --execute only after the
user explicitly approves an interactive OpenCV run.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import List, Sequence


class PreflightError(RuntimeError):
    """Raised for actionable preflight failures."""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Validate and optionally launch pytorch-yolo-v3 video/camera demo scripts without downloads."
    )
    p.add_argument("--repo-root", default=".", help="User checkout/source tree containing video_demo.py, video_demo_half.py, cam_demo.py, cfg/, data/, and pallete.")
    p.add_argument("--mode", choices=("video", "camera", "half"), default="video", help="Demo to prepare: video_demo.py, cam_demo.py, or video_demo_half.py.")
    p.add_argument("--video", default="video.avi", help="Video path for video/half modes, absolute or relative to --repo-root. Half mode source ignores custom values unless patched.")
    p.add_argument("--cfg", default="cfg/yolov3.cfg", help="Cfg path for video/half modes. Camera mode uses hard-coded cfg/yolov3.cfg.")
    p.add_argument("--weights", default="yolov3.weights", help="Local weights path for video/half modes. Camera mode uses hard-coded yolov3.weights.")
    p.add_argument("--dataset", default="pascal", help="Value passed to video/half --dataset.")
    p.add_argument("--confidence", type=float, default=None, help="Confidence threshold. Defaults: video/half 0.5, camera 0.25.")
    p.add_argument("--nms-thresh", type=float, default=0.4, help="NMS IoU threshold passed to --nms_thresh. Default: 0.4.")
    p.add_argument("--reso", type=int, default=None, help="Resolution. Defaults: video/half 416, camera 160; must be >32 and divisible by 32.")
    p.add_argument("--python", default=sys.executable, help="Python executable used when --execute is set. Default: current Python.")
    p.add_argument("--allow-display", action="store_true", help="Acknowledge that execution may open an OpenCV GUI window and wait for key input.")
    p.add_argument("--allow-camera", action="store_true", help="Acknowledge that camera mode may open OpenCV device 0.")
    p.add_argument("--accept-half-hardcode", action="store_true", help="Allow half mode execution even though video_demo_half.py hard-codes video.avi at runtime.")
    p.add_argument("--execute", action="store_true", help="Actually run the selected demo after preflight. Without this flag, only print the command.")
    return p


def resolve(repo_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path


def shell_join(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def rel_or_abs(repo_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def default_confidence(mode: str) -> float:
    return 0.25 if mode == "camera" else 0.5


def default_reso(mode: str) -> int:
    return 160 if mode == "camera" else 416


def validate_common(args: argparse.Namespace) -> tuple[Path, float, int, List[str]]:
    warnings: List[str] = []
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        raise PreflightError(f"--repo-root is not a directory: {repo_root}")
    confidence = default_confidence(args.mode) if args.confidence is None else args.confidence
    reso = default_reso(args.mode) if args.reso is None else args.reso
    if not (0.0 <= confidence < 1.0):
        raise PreflightError("confidence must be >= 0 and < 1")
    if not (0.0 <= args.nms_thresh <= 1.0):
        raise PreflightError("--nms-thresh must be between 0 and 1")
    if reso <= 32 or reso % 32 != 0:
        raise PreflightError("resolution must be greater than 32 and divisible by 32")
    if args.execute and not args.allow_display:
        raise PreflightError("execution opens an OpenCV window; pass --allow-display after user approval")
    return repo_root, confidence, reso, warnings


def validate_files(args: argparse.Namespace, repo_root: Path, warnings: List[str]) -> tuple[Path, List[str]]:
    if args.mode == "video":
        script = repo_root / "video_demo.py"
    elif args.mode == "half":
        script = repo_root / "video_demo_half.py"
    else:
        script = repo_root / "cam_demo.py"
    if not script.is_file():
        raise PreflightError(f"expected demo script is missing: {script.name}")

    if args.mode == "camera":
        cfg = repo_root / "cfg/yolov3.cfg"
        weights = repo_root / "yolov3.weights"
        if args.execute and not args.allow_camera:
            raise PreflightError("camera mode opens OpenCV device 0; pass --allow-camera after user approval")
        warnings.append("camera mode uses hard-coded cfg/yolov3.cfg and yolov3.weights in cam_demo.py")
    else:
        cfg = resolve(repo_root, args.cfg).resolve()
        weights = resolve(repo_root, args.weights).resolve()
        video = resolve(repo_root, args.video).resolve()
        if not video.is_file():
            raise PreflightError(f"video file does not exist: {video}")
        if args.mode == "half" and args.video != "video.avi":
            warnings.append("video_demo_half.py parses --video but hard-codes video.avi at runtime")
            if args.execute and not args.accept_half_hardcode:
                raise PreflightError("half mode custom --video would be ignored; pass --accept-half-hardcode only after handling that pitfall")
    if not cfg.is_file():
        raise PreflightError(f"cfg file does not exist: {cfg}")
    if not weights.is_file():
        raise PreflightError(f"weights file does not exist: {weights}; provide local weights before a full demo")
    return script, warnings


def command_for(args: argparse.Namespace, repo_root: Path, script: Path, confidence: float, reso: int) -> List[str]:
    command: List[str] = [args.python, str(script)]
    if args.mode in {"video", "half"}:
        command += [
            "--video",
            rel_or_abs(repo_root, resolve(repo_root, args.video).resolve()),
            "--dataset",
            args.dataset,
            "--cfg",
            rel_or_abs(repo_root, resolve(repo_root, args.cfg).resolve()),
            "--weights",
            rel_or_abs(repo_root, resolve(repo_root, args.weights).resolve()),
        ]
    command += [
        "--confidence",
        str(confidence),
        "--nms_thresh",
        str(args.nms_thresh),
        "--reso",
        str(reso),
    ]
    return command


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo_root, confidence, reso, warnings = validate_common(args)
        script, warnings = validate_files(args, repo_root, warnings)
    except PreflightError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 2

    command = command_for(args, repo_root, script, confidence, reso)
    print("pytorch-yolo-v3 video/camera wrapper")
    print("mode:", args.mode)
    print("execution:", "enabled" if args.execute else "dry-run")
    print("preflight: ok")
    for warning in warnings:
        print("WARNING:", warning)
    if args.mode == "camera":
        print("WARNING: cam_demo.py has a source-reviewed CUDA branch pitfall involving im_dim before assignment")
    if args.mode == "half":
        print("WARNING: half precision is optional and meaningful only with CUDA/fp16-capable hardware")
    print("command:")
    print("  " + shell_join(command))
    print("working_directory:", repo_root)
    print("notes: no weights were downloaded; execution may open an OpenCV display loop")

    if not args.execute:
        print("dry-run complete; add --execute plus --allow-display/--allow-camera only after user approval")
        return 0

    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    completed = subprocess.run(command, cwd=str(repo_root), env=env, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
