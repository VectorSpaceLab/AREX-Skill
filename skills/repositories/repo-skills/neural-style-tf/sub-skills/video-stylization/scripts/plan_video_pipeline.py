#!/usr/bin/env python3
"""Print a safe neural-style-tf video pipeline plan.

The original stylize_video.sh wrapper extracts frames, computes optical flow,
renders stylized frames, assembles a video, then deletes the temporary frame
folder. This planner is intentionally non-destructive: it prints commands and
placeholders so an operator can review paths before running expensive GPU/model
work.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path
from typing import List, Optional, Sequence


def q(parts: Sequence[object]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def expand(raw: str) -> Path:
    return Path(raw).expanduser()


def sanitize_basename(path: Path, provided: Optional[str]) -> str:
    if provided:
        name = provided
    else:
        name = path.name.rsplit(".", 1)[0] if path.name else "video"
    # Mirrors stylize_video.sh for percent characters; keep conservative shell-safe cleanup.
    name = name.replace("%", "x")
    for sep in ("/", os.sep):
        name = name.replace(sep, "_")
    return name or "video"


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print a non-destructive neural-style-tf video command plan.")
    parser.add_argument("--video", required=True, help="Input video path used for frame extraction planning.")
    parser.add_argument("--style", action="append", required=True, help="Style image path. Repeat for multiple styles.")
    parser.add_argument("--script", default="neural_style.py", help="Path to neural_style.py used in the printed render command.")
    parser.add_argument("--python", default="python", help="Python executable name in printed command.")
    parser.add_argument("--work-dir", default="./video_input", help="Working directory for extracted frames/flow files. Default: %(default)s")
    parser.add_argument("--output-dir", default="./video_output", help="Stylized frame/video output directory. Default: %(default)s")
    parser.add_argument("--basename", default=None, help="Override sanitized temp/output basename. By default uses video stem with %% replaced by x.")
    parser.add_argument("--start-frame", type=int, default=1)
    parser.add_argument("--end-frame", type=int, default=None, help="Last frame. If omitted, use frame count from ffprobe/after extraction.")
    parser.add_argument("--max-size", type=int, default=None, help="Optional --max_size for neural_style.py.")
    parser.add_argument("--device", choices=["/gpu:0", "/cpu:0"], default="/gpu:0", help="Device for printed neural_style.py command. Default follows repo recommendation.")
    parser.add_argument("--first-frame-iterations", type=int, default=None)
    parser.add_argument("--frame-iterations", type=int, default=None)
    parser.add_argument("--temporal-weight", type=float, default=None)
    parser.add_argument("--init-frame-type", choices=["prev_warped", "prev", "random", "content", "style"], default="prev_warped")
    parser.add_argument("--first-frame-type", choices=["random", "content", "style"], default="content")
    parser.add_argument("--ffmpeg-frame-pattern", default="frame_%04d.ppm", help="Extraction pattern for ffmpeg. Default: %(default)s")
    parser.add_argument("--content-frame-format", default="frame_{}.ppm", help="Python str.format template for neural_style.py. Default: %(default)s")
    parser.add_argument("--dry-run", action="store_true", help="Accepted for clarity; planner never executes by default.")
    parser.add_argument("--unsafe-run", action="store_true", help="Refuse execution with an explanation; this planner is intentionally non-destructive.")
    args = parser.parse_args(argv)
    if args.start_frame < 1:
        parser.error("--start-frame must be >= 1")
    if args.end_frame is not None and args.end_frame < args.start_frame:
        parser.error("--end-frame must be >= --start-frame")
    if args.max_size is not None and args.max_size <= 0:
        parser.error("--max-size must be positive")
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.unsafe_run:
        print(
            "error: this bundled planner does not execute video, optical-flow, cleanup, or rendering commands. "
            "Review the printed plan and run adapted commands manually in a prepared runtime.",
            file=sys.stderr,
        )
        return 2

    video = expand(args.video)
    script = expand(args.script)
    work_dir = expand(args.work_dir)
    output_dir = expand(args.output_dir)
    styles = [expand(s) for s in args.style]
    base = sanitize_basename(video, args.basename)
    temp_dir = work_dir / base
    output_video = output_dir / (base + "-stylized" + (video.suffix or ".mp4"))

    print("# neural-style-tf video plan (non-destructive)")
    print(f"# sanitized basename: {base}")
    print("# 1. Inspect input dimensions and frame count")
    print(q(["ffprobe", "-v", "error", "-of", "flat=s=_", "-select_streams", "v:0", "-show_entries", "stream=width,height", video]))
    print("# 2. Extract frames as PPM files")
    print(q(["mkdir", "-p", temp_dir]))
    print(q(["ffmpeg", "-v", "quiet", "-i", video, str(temp_dir / args.ffmpeg_frame_pattern)]))
    print("# 3. Generate optical-flow and reliability files if using prev_warped")
    if args.init_frame_type == "prev_warped":
        print("# Produce backward_{current}_{previous}.flo, forward_{previous}_{current}.flo, and reliable_*.txt files in:", temp_dir)
        print("# Use a compatible optical-flow tool; see references/optical-flow-files.md for expected names and formats.")
    else:
        print(f"# Optical flow not required for --init_frame_type {args.init_frame_type}; temporal consistency will be weaker.")

    style_dir = styles[0].parent if styles else Path(".")
    style_names: List[str] = []
    mixed_dirs = False
    for s in styles:
        style_names.append(s.name)
        if s.parent != style_dir:
            mixed_dirs = True
    if mixed_dirs:
        print("# WARNING: neural_style.py accepts one --style_imgs_dir; stage style images into one directory or adapt the command.", file=sys.stderr)

    end_frame = args.end_frame if args.end_frame is not None else "<num_frames>"
    command: List[object] = [
        args.python,
        script,
        "--video",
        "--video_input_dir",
        temp_dir,
        "--video_output_dir",
        output_dir,
        "--style_imgs_dir",
        style_dir,
        "--style_imgs",
        *style_names,
        "--start_frame",
        args.start_frame,
        "--end_frame",
        end_frame,
        "--content_frame_frmt",
        args.content_frame_format,
        "--first_frame_type",
        args.first_frame_type,
        "--init_frame_type",
        args.init_frame_type,
        "--device",
        args.device,
    ]
    if len(style_names) > 1:
        command.extend(["--style_imgs_weights", *("1.0" for _ in style_names)])
    if args.max_size is not None:
        command.extend(["--max_size", args.max_size])
    if args.first_frame_iterations is not None:
        command.extend(["--first_frame_iterations", args.first_frame_iterations])
    if args.frame_iterations is not None:
        command.extend(["--frame_iterations", args.frame_iterations])
    if args.temporal_weight is not None:
        command.extend(["--temporal_weight", args.temporal_weight])

    print("# 4. Render stylized frames")
    print(q(command))
    print("# 5. Assemble stylized frames into a video")
    print(q(["mkdir", "-p", output_dir]))
    print(q(["ffmpeg", "-v", "quiet", "-i", str(output_dir / args.ffmpeg_frame_pattern), output_video]))
    print("# 6. Cleanup is intentionally omitted. Inspect temporary files before deleting:", temp_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
