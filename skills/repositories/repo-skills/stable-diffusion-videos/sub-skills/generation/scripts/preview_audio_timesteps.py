#!/usr/bin/env python3
"""Preview stable-diffusion-videos audio interpolation weights."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_filepath", type=Path, help="Local audio file to analyze.")
    parser.add_argument("--offset", type=float, default=0.0, help="Start offset in seconds.")
    parser.add_argument("--duration", type=float, required=True, help="Duration in seconds to analyze.")
    parser.add_argument("--fps", type=int, default=30, help="Output frames per second.")
    parser.add_argument("--margin", type=float, default=1.0, help="librosa HPSS margin value.")
    parser.add_argument("--smooth", type=float, default=0.0, help="Blend toward a linear ramp; 1.0 is fully linear.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.audio_filepath.exists():
        raise SystemExit(f"audio file not found: {args.audio_filepath}")
    if args.duration <= 0:
        raise SystemExit("--duration must be positive")
    if args.fps <= 0:
        raise SystemExit("--fps must be positive")

    from stable_diffusion_videos import get_timesteps_arr

    arr = get_timesteps_arr(
        args.audio_filepath,
        offset=args.offset,
        duration=args.duration,
        fps=args.fps,
        margin=args.margin,
        smooth=args.smooth,
    )

    payload = {
        "audio_filepath": str(args.audio_filepath),
        "offset": args.offset,
        "duration": args.duration,
        "fps": args.fps,
        "frame_count": int(arr.shape[0]),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "first": float(arr[0]),
        "last": float(arr[-1]),
        "sample": [float(x) for x in arr[: min(8, arr.shape[0])]],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"audio={payload['audio_filepath']}")
        print(f"offset={payload['offset']} duration={payload['duration']} fps={payload['fps']}")
        print(f"frame_count={payload['frame_count']} min={payload['min']:.6f} max={payload['max']:.6f}")
        print(f"first={payload['first']:.6f} last={payload['last']:.6f}")
        print("sample=" + ", ".join(f"{x:.6f}" for x in payload["sample"]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
