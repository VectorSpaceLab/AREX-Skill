#!/usr/bin/env python3
"""Validate assets and build a Blender argv; dry-run is the default."""
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True, help="user checkout containing blender_rendering")
    parser.add_argument("--blender", default="blender")
    parser.add_argument("--mode", choices=["load", "render", "skin", "fbx2bvh"], required=True)
    parser.add_argument("--bvh-file", type=Path)
    parser.add_argument("--fbx-file", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--engine", choices=["cycles", "eevee"], default="cycles")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--frame-end", type=int, default=100)
    parser.add_argument("--res-x", type=int, default=960)
    parser.add_argument("--res-y", type=int, default=540)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.frame_end < 1 or args.res_x < 1 or args.res_y < 1:
        print("preflight failed: frame-end and resolution must be positive")
        return 2
    root = args.repo_root.expanduser().resolve()
    scripts = {
        "load": root / "blender_rendering" / "render.py",
        "render": root / "blender_rendering" / "render.py",
        "skin": root / "blender_rendering" / "skinning.py",
    }
    if args.mode == "fbx2bvh":
        # This is a skill-owned single-file replacement for the source helper's
        # bulk, hard-coded directory traversal.
        script = Path(__file__).with_name("fbx_to_bvh.py").resolve()
    else:
        script = scripts[args.mode]
    if not script.is_file():
        print(f"preflight failed: missing script {script}")
        return 2
    if args.mode in {"load", "render", "skin"} and (not args.bvh_file or not args.bvh_file.is_file()):
        print("preflight failed: load/render/skin require an existing --bvh-file")
        return 2
    if args.mode in {"skin", "fbx2bvh"} and (not args.fbx_file or not args.fbx_file.is_file()):
        print("preflight failed: skin/fbx2bvh require an existing --fbx-file")
        return 2
    if args.mode in {"render", "fbx2bvh"} and not args.output:
        print(f"preflight failed: {args.mode} requires a new --output path")
        return 2
    if args.output and args.output.exists() and not args.force:
        print(f"preflight failed: output exists; choose a new path or pass --force: {args.output}")
        return 2

    # Load/render use render.py because the upstream load_bvh.py main block
    # ignores CLI arguments and always opens ./example.bvh. Skinning is an
    # interactive scene operation, so it intentionally does not use --background.
    command = [args.blender]
    if args.mode in {"render", "fbx2bvh"}:
        command.append("--background")
    command += ["--python", str(script), "--"]
    if args.mode in {"load", "render"}:
        command += ["--bvh_path", str(args.bvh_file)]
    if args.mode == "render":
        command += ["--save_path", str(args.output), "--render_engine", args.engine,
                    "--frame_end", str(args.frame_end), "--resX", str(args.res_x),
                    "--resY", str(args.res_y)]
        if args.render:
            command += ["--render"]
    elif args.mode == "skin":
        command += ["--fbx_file", str(args.fbx_file), "--bvh_file", str(args.bvh_file)]
    elif args.mode == "fbx2bvh":
        command += ["--fbx-file", str(args.fbx_file), "--output", str(args.output)]
        if args.force:
            command.append("--force")

    print(json.dumps({"mode": args.mode, "command": command, "shell_preview": shlex.join(command)}, indent=2))
    print("dry-run only; Blender, bpy, assets, and output safety must be reviewed before --execute")
    if not args.execute:
        return 0
    if shutil.which(args.blender) is None:
        print(f"execution failed: Blender executable not found: {args.blender}")
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(command, cwd=root / "blender_rendering", check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
