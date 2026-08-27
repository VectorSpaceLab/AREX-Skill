#!/usr/bin/env python3
"""Validated launcher for AdelaiDet tools/visualize_data.py."""

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
    parser = argparse.ArgumentParser(description="Run AdelaiDet dataset visualization")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--config", required=True, help="Config YAML, absolute or relative to repo root")
    parser.add_argument("--source", default="dataloader", help="Visualization source passed to repository script")
    parser.add_argument("--output", default="output/visualize_data", help="Output directory")
    parser.add_argument("--show", action="store_true", help="Ask repository script to show windows")
    parser.add_argument("--opts", nargs=argparse.REMAINDER, default=[], help="Extra config KEY VALUE pairs")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo_root).resolve()
    script = repo / "tools" / "visualize_data.py"
    if not script.exists():
        raise SystemExit(f"missing visualize_data.py: {script}")
    config = resolve_existing(repo, args.config, "config")
    cmd = [
        sys.executable,
        str(script),
        "--config-file",
        str(config),
        "--source",
        args.source,
        "--output-dir",
        args.output,
    ]
    if args.show:
        cmd.append("--show")
    cmd.extend(args.opts)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    print(" ".join(shlex.quote(part) for part in cmd))
    if args.dry_run:
        return 0
    return subprocess.call(cmd, cwd=str(repo), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
