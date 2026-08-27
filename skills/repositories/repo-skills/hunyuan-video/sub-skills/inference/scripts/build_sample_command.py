#!/usr/bin/env python3
"""Build a HunyuanVideo sampling command without running generation.

The emitted command uses the bundled run_sample_video.py replacement instead of
the source repository's sample_video.py, so future agents can pass an explicit
--repo-root and avoid depending on a particular current working directory.
"""

from __future__ import annotations

import argparse
import json
import shlex
from typing import List


def validate_4n1(value: int) -> None:
    if value <= 0:
        raise argparse.ArgumentTypeError("video length must be positive")
    if value != 1 and (value - 1) % 4 != 0:
        raise argparse.ArgumentTypeError("default 884 VAE requires video_length == 1 or (video_length - 1) % 4 == 0")


def command_list(args: argparse.Namespace) -> List[str]:
    cmd = [
        "python", args.runner,
    ]
    if args.repo_root:
        cmd += ["--repo-root", args.repo_root]
    cmd += [
        "--model-base", args.model_base,
        "--video-size", str(args.height), str(args.width),
        "--video-length", str(args.video_length),
        "--infer-steps", str(args.infer_steps),
        "--prompt", args.prompt,
        "--embedded-cfg-scale", str(args.embedded_cfg_scale),
        "--flow-shift", str(args.flow_shift),
        "--save-path", args.save_path,
    ]
    if args.seed is not None:
        cmd += ["--seed", str(args.seed)]
    if args.cfg_scale is not None:
        cmd += ["--cfg-scale", str(args.cfg_scale)]
    if args.num_videos != 1:
        cmd += ["--num-videos", str(args.num_videos)]
    if args.batch_size != 1:
        cmd += ["--batch-size", str(args.batch_size)]
    if args.flow_reverse:
        cmd.append("--flow-reverse")
    if args.use_cpu_offload:
        cmd.append("--use-cpu-offload")
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a validated HunyuanVideo single-GPU sample command.")
    parser.add_argument("--prompt", required=True, help="Text prompt for generation.")
    parser.add_argument("--height", type=int, default=544, help="Video height; passed as first --video-size value.")
    parser.add_argument("--width", type=int, default=960, help="Video width; passed as second --video-size value.")
    parser.add_argument("--video-length", type=int, default=129, help="Frame count; default VAE requires 4n+1.")
    parser.add_argument("--infer-steps", type=int, default=50)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--repo-root", default=None, help="Optional HunyuanVideo source root passed to the bundled runner; omit when hyvideo is installed/importable.")
    parser.add_argument("--runner", default=None, help="Path to the bundled run_sample_video.py helper. Defaults to the sibling helper next to this script.")
    parser.add_argument("--model-base", default="ckpts")
    parser.add_argument("--save-path", default="./results")
    parser.add_argument("--embedded-cfg-scale", type=float, default=6.0)
    parser.add_argument("--flow-shift", type=float, default=7.0)
    parser.add_argument("--cfg-scale", type=float, default=None)
    parser.add_argument("--num-videos", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--no-flow-reverse", dest="flow_reverse", action="store_false", help="Omit --flow-reverse. Default includes it because repo examples do.")
    parser.set_defaults(flow_reverse=True)
    parser.add_argument("--use-cpu-offload", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print JSON with command array and shell string.")
    args = parser.parse_args()

    if args.height <= 0 or args.width <= 0:
        parser.error("height and width must be positive")
    try:
        validate_4n1(args.video_length)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    if args.infer_steps <= 0:
        parser.error("infer steps must be positive")
    if args.num_videos <= 0 or args.batch_size <= 0:
        parser.error("num-videos and batch-size must be positive")

    if args.runner is None:
        args.runner = "sub-skills/inference/scripts/run_sample_video.py"
    cmd = command_list(args)
    shell = shlex.join(cmd)
    if args.json:
        print(json.dumps({"command": cmd, "shell": shell}, indent=2))
    else:
        print(shell)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
