#!/usr/bin/env python3
"""Blender-only single-file FBX-to-BVH adapter.

Run through Blender, not ordinary Python:
  blender --background --python fbx_to_bvh.py -- --fbx-file in.fbx --output out.bvh
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def script_argv() -> list[str]:
    # Blender places script arguments after a second `--`; ordinary Python
    # help/parser checks do not, so retain sys.argv[1:] in that case.
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fbx-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(script_argv())
    if not args.fbx_file.is_file() or args.fbx_file.suffix.lower() != ".fbx":
        parser.error("--fbx-file must be an existing .fbx file")
    if args.output.suffix.lower() != ".bvh":
        parser.error("--output must end in .bvh")
    if args.output.exists() and not args.force:
        parser.error("output exists; choose a new path or pass --force")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        import bpy
    except ImportError as exc:
        parser.error(f"bpy is unavailable; run this script through Blender: {exc}")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.fbx(filepath=str(args.fbx_file.resolve()))
    if not bpy.data.actions:
        parser.error("the imported FBX exposes no animation action")
    starts = [float(action.frame_range[0]) for action in bpy.data.actions]
    ends = [float(action.frame_range[1]) for action in bpy.data.actions]
    bpy.ops.export_anim.bvh(
        filepath=str(args.output.resolve()),
        frame_start=int(min(starts)),
        frame_end=max(60, int(max(ends))),
        root_transform_only=True,
    )
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
