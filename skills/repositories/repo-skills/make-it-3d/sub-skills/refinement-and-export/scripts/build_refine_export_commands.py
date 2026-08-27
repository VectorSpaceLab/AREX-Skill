#!/usr/bin/env python3
"""Emit Make-It-3D refinement, test-render, and mesh-export commands."""
from __future__ import annotations

import argparse
import json
import shlex
from typing import Dict, List


def q(value: object) -> str:
    return shlex.quote(str(value))


def common_args(args: argparse.Namespace) -> List[str]:
    parts = ["python", "main.py", "--workspace", args.workspace, "--ref_path", args.ref_path]
    if args.text:
        parts += ["--text", args.text]
    if args.negative:
        parts += ["--negative", args.negative]
    if args.fp16:
        parts.append("--fp16")
    if args.vanilla_backbone:
        parts += ["--backbone", "vanilla"]
    return parts


def build(args: argparse.Namespace) -> Dict[str, List[str]]:
    base = common_args(args)
    refine = base + ["--phi_range", str(args.refine_phi_min), str(args.refine_phi_max), "--final", "--refine", "--refine_iters", str(args.refine_iters)]
    test = base + ["--test"]
    mesh = base + ["--test", "--save_mesh"]
    commands = {"refine_stage": refine, "test_render": test}
    if args.save_mesh:
        commands["mesh_export"] = mesh
    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Make-It-3D refine/test/export commands")
    parser.add_argument("--workspace", required=True, help="Existing workspace name; source reads/writes results/<workspace>")
    parser.add_argument("--ref-path", required=True, help="Reference alpha image path")
    parser.add_argument("--text", default=None, help="Prompt text; recommended to avoid BLIP2")
    parser.add_argument("--negative", default=None)
    parser.add_argument("--refine-iters", type=int, default=3000)
    parser.add_argument("--refine-phi-min", type=float, default=135)
    parser.add_argument("--refine-phi-max", type=float, default=225)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--vanilla-backbone", action="store_true")
    parser.add_argument("--save-mesh", action="store_true", help="Also print a mesh export command")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    commands = build(args)
    if args.json:
        print(json.dumps(commands, indent=2))
    else:
        print("# Run from the user's Make-It-3D checkout after coarse checkpoints exist.")
        print("# The refine command includes --final because the inspected source nests refine execution under if opt.final.")
        for label, command in commands.items():
            print(f"\n# {label.replace('_', ' ').title()}")
            print(" ".join(q(part) for part in command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
