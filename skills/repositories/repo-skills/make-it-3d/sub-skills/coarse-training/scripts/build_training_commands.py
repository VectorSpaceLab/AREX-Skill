#!/usr/bin/env python3
"""Emit Make-It-3D coarse-stage training commands."""
from __future__ import annotations

import argparse
import json
import shlex
from typing import Dict, List


def q(value: object) -> str:
    return shlex.quote(str(value))


def build(args: argparse.Namespace) -> Dict[str, List[str]]:
    common = ["python", "main.py", "--workspace", args.workspace, "--ref_path", args.ref_path]
    if args.text:
        common += ["--text", args.text]
    if args.negative:
        common += ["--negative", args.negative]
    common += ["--guidance", args.guidance, "--sd_version", args.sd_version]
    if args.hf_key:
        common += ["--hf_key", args.hf_key]
    if args.need_back:
        common.append("--need_back")
    if args.fp16:
        common.append("--fp16")
    if args.vanilla_backbone:
        common += ["--backbone", "vanilla"]
    if args.seed is not None:
        common += ["--seed", str(args.seed)]

    first = common + ["--phi_range", str(args.front_phi_min), str(args.front_phi_max), "--iters", str(args.first_iters)]
    if args.geometry_rescue:
        first += ["--fov", str(args.fov), "--fovy_range", str(args.fovy_min), str(args.fovy_max), "--blob_radius", str(args.blob_radius)]
    final = common + ["--phi_range", "0", "360", "--albedo_iters", str(args.albedo_iters), "--iters", str(args.final_iters), "--final"]
    return {"front_stage": first, "full_360_stage": final}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Make-It-3D README-backed coarse training commands")
    parser.add_argument("--workspace", required=True, help="Workspace name; source writes under results/<workspace>")
    parser.add_argument("--ref-path", required=True, help="Reference alpha image path as it should appear in the runtime command")
    parser.add_argument("--text", default=None, help="Prompt text; recommended to avoid BLIP2 captioning")
    parser.add_argument("--negative", default=None, help="Negative prompt")
    parser.add_argument("--guidance", default="stable-diffusion", choices=["stable-diffusion", "clip"])
    parser.add_argument("--sd-version", default="2.0", choices=["1.5", "2.0"])
    parser.add_argument("--hf-key", default=None, help="Custom Hugging Face model id")
    parser.add_argument("--need-back", action="store_true", help="Add back-view prompt conditioning")
    parser.add_argument("--fp16", action="store_true", help="Emit mixed precision flag")
    parser.add_argument("--vanilla-backbone", action="store_true", help="Emit --backbone vanilla to avoid tinycudann default backbone")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--first-iters", type=int, default=2000)
    parser.add_argument("--final-iters", type=int, default=5000)
    parser.add_argument("--albedo-iters", type=int, default=3500)
    parser.add_argument("--front-phi-min", type=float, default=135)
    parser.add_argument("--front-phi-max", type=float, default=225)
    parser.add_argument("--geometry-rescue", action="store_true", help="Use README long-geometry rescue settings in the front-stage command")
    parser.add_argument("--fov", type=float, default=60)
    parser.add_argument("--fovy-min", type=float, default=50)
    parser.add_argument("--fovy-max", type=float, default=70)
    parser.add_argument("--blob-radius", type=float, default=0.2)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    commands = build(args)
    if args.json:
        print(json.dumps(commands, indent=2))
    else:
        print("# Run from the user's Make-It-3D checkout after environment/assets/input checks.")
        for label, command in commands.items():
            print(f"\n# {label.replace('_', ' ').title()}")
            print(" ".join(q(part) for part in command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
