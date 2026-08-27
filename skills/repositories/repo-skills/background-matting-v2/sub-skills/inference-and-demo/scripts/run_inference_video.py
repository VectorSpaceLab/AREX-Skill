#!/usr/bin/env python3
"""Dry-run or launch the checkout's video inference CLI through a checked wrapper.

Safe by default:
- prints the command unless --execute is given
- requires an explicit --repo-root
- forwards all extra arguments after `--`

Example:
    python sub-skills/inference-and-demo/scripts/run_inference_video.py \
      --repo-root /path/to/BackgroundMattingV2 --dry-run -- \
      --model-type mattingrefine --model-backbone mobilenetv2 ...
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    p = argparse.ArgumentParser(description="Launch BackgroundMattingV2 video inference")
    p.add_argument("--repo-root", required=True)
    p.add_argument("--python", default=sys.executable)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args, remainder = p.parse_known_args()
    if remainder and remainder[0] == "--":
        remainder = remainder[1:]
    return args, remainder


def main() -> int:
    args, passthrough = parse_args()
    repo_root = Path(args.repo_root).resolve()
    script = repo_root / "inference_video.py"
    if not repo_root.exists():
        print(f"repo-root does not exist: {repo_root}", file=sys.stderr)
        return 2
    if not script.exists():
        print(f"video inference entry not found: {script}", file=sys.stderr)
        return 3

    cmd = [args.python, str(script), *passthrough]
    print(shlex.join(cmd))
    if args.dry_run or not args.execute:
        return 0

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
