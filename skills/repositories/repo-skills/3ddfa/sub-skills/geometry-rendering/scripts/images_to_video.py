#!/usr/bin/env python3
"""Assemble a sorted image sequence into an MP4 video.

The helper uses explicit input and output arguments so it can be reused for
render-frame folders without depending on any repository-relative defaults.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a directory of rendered images into a video."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Directory containing the source image frames.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output video path, usually ending in .mp4.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="Frames per second for the output video.",
    )
    parser.add_argument(
        "--pattern",
        default="*.jpg",
        help="Glob pattern for the image frames inside --input-dir.",
    )
    return parser.parse_args()


def frame_sort_key(path: Path) -> tuple[int, int | str, str]:
    match = re.search(r"(\d+)(?!.*\d)", path.stem)
    if match:
        return (0, int(match.group(1)), path.stem)
    return (1, path.stem, path.stem)


def collect_frames(input_dir: Path, pattern: str) -> list[Path]:
    frames = sorted(input_dir.glob(pattern), key=frame_sort_key)
    if not frames:
        raise FileNotFoundError(
            f"no frames matched pattern {pattern!r} in {input_dir}"
        )
    return frames


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not input_dir.is_dir():
        raise NotADirectoryError(f"input directory does not exist: {input_dir}")

    try:
        import imageio.v2 as imageio
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "imageio is required to write videos; install it in the active environment"
        ) from exc

    frames = collect_frames(input_dir, args.pattern)
    images = [imageio.imread(frame) for frame in frames]
    output.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimwrite(output, images, fps=args.fps, macro_block_size=None)
    print(f"wrote {output} from {len(images)} frames")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
