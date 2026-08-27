#!/usr/bin/env python3
"""Inspect and optionally exercise the video decode helpers."""

from __future__ import annotations

import argparse
import inspect
import json
import os
from pathlib import Path

from lmms_eval.models.model_utils import load_video as load_video_mod
from lmms_eval.models.model_utils.load_video import read_video


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect lmms-eval video decode backends.")
    parser.add_argument("--video", type=Path, help="Optional local video file to decode.")
    parser.add_argument("--backend", default=None, help="Backend to pass to read_video.")
    parser.add_argument("--num-frm", type=int, default=4, help="Number of frames to sample when decoding a video.")
    parser.add_argument("--fps", type=float, default=None, help="Optional decode FPS.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    args = parser.parse_args()

    report = {
        "env_backend": os.environ.get("LMMS_VIDEO_DECODE_BACKEND"),
        "helpers": {
            name: hasattr(load_video_mod, name)
            for name in (
                "read_video_torchcodec",
                "read_video_dali",
                "load_video_decord",
                "load_video_stream",
                "load_video_packet",
            )
        },
        "read_video_signature": str(inspect.signature(read_video)),
    }

    if args.video is not None:
        if not args.video.exists():
            raise SystemExit(f"video file not found: {args.video}")
        frames = read_video(
            str(args.video),
            num_frm=args.num_frm,
            fps=args.fps,
            backend=args.backend,
        )
        report["decode"] = {
            "path": str(args.video),
            "backend": args.backend,
            "shape": getattr(frames, "shape", None),
            "dtype": getattr(frames, "dtype", None),
        }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"LMMS_VIDEO_DECODE_BACKEND={report['env_backend']!r}")
        print("helpers:", ", ".join(name for name, enabled in report["helpers"].items() if enabled))
        if "decode" in report:
            print(f"decoded {report['decode']['path']} -> {report['decode']['shape']} ({report['decode']['dtype']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
