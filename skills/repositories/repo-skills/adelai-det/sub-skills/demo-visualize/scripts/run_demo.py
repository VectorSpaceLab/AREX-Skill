#!/usr/bin/env python3
"""Validated launcher for AdelaiDet demo/demo.py."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


def resolve_existing(base: Path, value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    if not path.exists():
        raise SystemExit(f"{label} does not exist: {path}")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AdelaiDet demo with preflight checks")
    parser.add_argument("--repo-root", required=True, help="AdelaiDet source checkout root")
    parser.add_argument("--config", required=True, help="Config YAML, absolute or relative to repo root")
    parser.add_argument("--weights", required=True, help="Model weights path")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--input", nargs="+", help="Input image path(s) or patterns")
    mode.add_argument("--video-input", help="Video input path")
    mode.add_argument("--webcam", action="store_true", help="Use webcam mode")
    parser.add_argument("--output", help="Output file or directory")
    parser.add_argument("--confidence-threshold", type=float, default=0.3)
    parser.add_argument("--opts", nargs=argparse.REMAINDER, default=[], help="Extra config KEY VALUE pairs")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo_root).resolve()
    demo_py = repo / "demo" / "demo.py"
    if not demo_py.exists():
        raise SystemExit(f"missing AdelaiDet demo script: {demo_py}")
    config = resolve_existing(repo, args.config, "config")
    weights = resolve_existing(repo, args.weights, "weights")

    cmd = [
        sys.executable,
        str(demo_py),
        "--config-file",
        str(config),
        "--confidence-threshold",
        str(args.confidence_threshold),
    ]
    if args.input:
        for item in args.input:
            if not any(ch in item for ch in "*?[]"):
                resolve_existing(repo, item, "input")
        cmd.extend(["--input", *args.input])
    elif args.video_input:
        video = resolve_existing(repo, args.video_input, "video input")
        cmd.extend(["--video-input", str(video)])
    else:
        cmd.append("--webcam")

    if args.output:
        cmd.extend(["--output", args.output])
    cmd.extend(["--opts", "MODEL.WEIGHTS", str(weights), *args.opts])

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    print(" ".join(shlex.quote(part) for part in cmd))
    if args.dry_run:
        return 0
    return subprocess.call(cmd, cwd=str(repo), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
