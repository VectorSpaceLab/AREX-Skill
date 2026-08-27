#!/usr/bin/env python3
"""Compose a PPO GIF from already-saved frame images.

This helper adapts the repository's GIF-composition logic into a small CLI
that only needs Pillow and a directory of ordered frame images. It does not
capture frames from a live Gym environment.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from glob import glob
from pathlib import Path
from typing import List, Optional

from PIL import Image


@dataclass
class GifResolution:
    images_glob: str
    output_path: str
    total_timesteps: Optional[int]
    step: int
    frame_duration: int
    frame_count: int
    warnings: List[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compose a GIF from saved PPO frame images.")
    parser.add_argument("--images-glob", required=True, help="Glob pattern for frame images, for example 'PPO_gif_images/CartPole-v1/*.jpg'.")
    parser.add_argument("--output", required=True, help="Output GIF path.")
    parser.add_argument("--total-timesteps", type=int, help="Optional upper bound on the number of frames to consider before stepping.")
    parser.add_argument("--step", type=int, default=10, help="Subsample every Nth frame before composing the GIF.")
    parser.add_argument("--frame-duration", type=int, default=150, help="Frame duration in milliseconds.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    return parser


def resolve(args: argparse.Namespace) -> GifResolution:
    warnings: List[str] = []
    frame_paths = sorted(glob(args.images_glob))
    if args.total_timesteps is not None:
        frame_paths = frame_paths[: args.total_timesteps]
    if args.step <= 0:
        raise ValueError("--step must be a positive integer")
    frame_paths = frame_paths[:: args.step]
    if not frame_paths:
        warnings.append("No frames resolved from the requested glob.")
    return GifResolution(
        images_glob=args.images_glob,
        output_path=args.output,
        total_timesteps=args.total_timesteps,
        step=args.step,
        frame_duration=args.frame_duration,
        frame_count=len(frame_paths),
        warnings=warnings,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    resolution = resolve(args)

    if args.json:
        print(json.dumps(asdict(resolution), indent=2, sort_keys=True))
        return 0

    print("PPO GIF composition helper")
    print("=" * 79)
    print(f"images_glob: {resolution.images_glob}")
    print(f"output_path: {resolution.output_path}")
    print(f"total_timesteps: {resolution.total_timesteps}")
    print(f"step: {resolution.step}")
    print(f"frame_duration: {resolution.frame_duration}")
    print(f"frame_count: {resolution.frame_count}")
    if resolution.warnings:
        print("warnings:")
        for warning in resolution.warnings:
            print(f"  - {warning}")

    if resolution.frame_count == 0:
        return 2

    frame_paths = sorted(glob(resolution.images_glob))
    if resolution.total_timesteps is not None:
        frame_paths = frame_paths[: resolution.total_timesteps]
    frame_paths = frame_paths[:: resolution.step]

    Path(resolution.output_path).parent.mkdir(parents=True, exist_ok=True)
    first, *rest = [Image.open(path) for path in frame_paths]
    first.save(
        fp=resolution.output_path,
        format="GIF",
        append_images=rest,
        save_all=True,
        optimize=True,
        duration=resolution.frame_duration,
        loop=0,
    )
    print(f"saved gif at: {resolution.output_path}")
    print("=" * 79)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
