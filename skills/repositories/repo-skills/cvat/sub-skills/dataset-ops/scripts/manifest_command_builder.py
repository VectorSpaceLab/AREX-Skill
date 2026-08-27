#!/usr/bin/env python3
"""Build safe CVAT dataset-manifest command shapes.

The helper prints a shell-quoted command and does not create a manifest. By default it
uses a module-style entry point (`python -m dataset_manifest.create`) so the caller can
supply an installed or bundled manifest utility without depending on an original CVAT
source checkout. Override --tool when your deployment provides a different command.
"""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


def quote(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts if part)


def split_tool(tool: str) -> list[str]:
    return shlex.split(tool)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tool",
        default="python -m dataset_manifest.create",
        help="manifest tool command prefix; default: python -m dataset_manifest.create",
    )
    sub = parser.add_subparsers(dest="kind", required=True)

    img = sub.add_parser("images", help="build a manifest command for an image directory or glob")
    img.add_argument("source", help="directory or glob pattern of images")
    img.add_argument("--output-dir", default="manifest", help="manifest output directory")
    img.add_argument(
        "--sorting",
        choices=("lexicographical", "natural", "predefined", "random"),
        default="lexicographical",
    )

    vid = sub.add_parser("video", help="build a manifest command for a video file")
    vid.add_argument("source", help="video file path")
    vid.add_argument("--output-dir", default="manifest", help="manifest output directory")
    vid.add_argument("--force", action="store_true", help="allow manifest creation for weak keyframe layouts")

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    cmd = split_tool(args.tool) + ["--output-dir", str(output_dir)]
    if args.kind == "images":
        cmd += ["--sorting", args.sorting, args.source]
    else:
        if args.force:
            cmd.append("--force")
        cmd.append(args.source)

    print(quote(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
