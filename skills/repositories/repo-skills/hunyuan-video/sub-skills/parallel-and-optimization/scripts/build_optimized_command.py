#!/usr/bin/env python3
"""Build validated HunyuanVideo xDiT or FP8 commands without running them."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import List


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--repo-root", default=None, help="Optional HunyuanVideo source root; omit when hyvideo is installed/importable.")
    parser.add_argument("--runner", default="sub-skills/inference/scripts/run_sample_video.py")
    parser.add_argument("--model-base", default="ckpts")
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--video-length", type=int, default=129)
    parser.add_argument("--infer-steps", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--save-path", default="./results")
    parser.add_argument("--embedded-cfg-scale", type=float, default=6.0)
    parser.add_argument("--flow-shift", type=float, default=7.0)
    parser.add_argument("--json", action="store_true")


def base_runner(args: argparse.Namespace) -> List[str]:
    cmd = [args.runner]
    if args.repo_root:
        cmd += ["--repo-root", args.repo_root]
    cmd += [
        "--model-base", args.model_base,
        "--video-size", str(args.height), str(args.width),
        "--video-length", str(args.video_length),
        "--infer-steps", str(args.infer_steps),
        "--prompt", args.prompt,
        "--seed", str(args.seed),
        "--embedded-cfg-scale", str(args.embedded_cfg_scale),
        "--flow-shift", str(args.flow_shift),
        "--flow-reverse",
        "--save-path", args.save_path,
    ]
    return cmd


def validate_frames(parser: argparse.ArgumentParser, length: int) -> None:
    if length <= 0 or (length != 1 and (length - 1) % 4 != 0):
        parser.error("default 884 VAE requires video_length == 1 or (video_length - 1) % 4 == 0")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print validated HunyuanVideo optimization commands.")
    sub = parser.add_subparsers(dest="mode", required=True)
    p_multi = sub.add_parser("multi-gpu", help="Build a torchrun xDiT command.")
    add_common(p_multi)
    p_multi.add_argument("--nproc-per-node", type=int, required=True)
    p_multi.add_argument("--ulysses-degree", type=int, required=True)
    p_multi.add_argument("--ring-degree", type=int, required=True)

    p_fp8 = sub.add_parser("fp8", help="Build a single-GPU FP8 command.")
    add_common(p_fp8)
    p_fp8.add_argument("--dit-weight", required=True, help="Path to *_fp8.pt DIT weight file.")
    p_fp8.add_argument("--use-cpu-offload", action="store_true")
    p_fp8.add_argument("--skip-map-existence-check", action="store_true", help="Only derive and print the map path; do not require local existence.")

    args = parser.parse_args()
    validate_frames(parser, args.video_length)
    if args.height <= 0 or args.width <= 0:
        parser.error("height and width must be positive")

    if args.mode == "multi-gpu":
        if args.nproc_per_node != args.ulysses_degree * args.ring_degree:
            parser.error("--nproc-per-node must equal --ulysses-degree * --ring-degree")
        cmd = ["torchrun", f"--nproc_per_node={args.nproc_per_node}"] + base_runner(args) + [
            "--ulysses-degree", str(args.ulysses_degree),
            "--ring-degree", str(args.ring_degree),
        ]
        extra = {"degree_product": args.ulysses_degree * args.ring_degree}
    else:
        fp8 = Path(args.dit_weight).expanduser()
        if fp8.suffix != ".pt":
            parser.error("--dit-weight should point to the *_fp8.pt file")
        map_path = fp8.with_name(fp8.name[:-3] + "_map.pt")
        if not args.skip_map_existence_check and not map_path.exists():
            parser.error(f"FP8 map file is missing: {map_path}. Use --skip-map-existence-check only for remote/planned paths.")
        cmd = ["python"] + base_runner(args) + ["--dit-weight", str(fp8), "--use-fp8"]
        if args.use_cpu_offload:
            cmd.append("--use-cpu-offload")
        extra = {"fp8_map": str(map_path)}

    shell = shlex.join(cmd)
    if args.json:
        print(json.dumps({"command": cmd, "shell": shell, **extra}, indent=2))
    else:
        print(shell)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
