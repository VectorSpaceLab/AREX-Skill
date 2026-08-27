#!/usr/bin/env python3
"""Preflight and optionally launch DragGAN's Gradio visualizer."""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight and launch DragGAN Gradio demo.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Local DragGAN checkout containing visualizer_drag_gradio.py.")
    parser.add_argument("--cache-dir", type=Path, default=Path("checkpoints"), help="Directory containing .pkl checkpoints, relative to repo root unless absolute.")
    parser.add_argument("--listen", action="store_true", help="Pass --listen so Gradio binds to 0.0.0.0.")
    parser.add_argument("--share", action="store_true", help="Pass --share to request a Gradio share link.")
    parser.add_argument("--execute", action="store_true", help="Actually start the Gradio app. Without this flag the command is printed only.")
    args = parser.parse_args()

    repo_root = args.repo_root.expanduser().resolve()
    script = repo_root / "visualizer_drag_gradio.py"
    if not script.exists():
        print(f"ERROR: cannot find visualizer_drag_gradio.py under repo root: {repo_root}", file=sys.stderr)
        return 2

    cache_dir = args.cache_dir.expanduser()
    if not cache_dir.is_absolute():
        cache_dir = repo_root / cache_dir
    cache_dir = cache_dir.resolve()
    pkls = sorted(cache_dir.glob("*.pkl")) if cache_dir.exists() else []
    if not pkls:
        print(f"ERROR: Gradio initialization expects at least one .pkl checkpoint in: {cache_dir}", file=sys.stderr)
        print("Run a checkpoint download outside this helper or pass --cache-dir pointing at existing model files.", file=sys.stderr)
        return 3

    cmd = [sys.executable, str(script), "--cache-dir", str(cache_dir)]
    if args.listen:
        cmd.append("--listen")
    if args.share:
        cmd.append("--share")

    print("Found checkpoint candidates:")
    for p in pkls:
        print(f"- {p.name}")
    print("Command:")
    print(" ".join(shlex.quote(part) for part in cmd))
    if args.execute:
        return subprocess.call(cmd, cwd=str(repo_root))
    print("Dry run only. Pass --execute to start the Gradio app.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
