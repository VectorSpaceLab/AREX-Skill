#!/usr/bin/env python3
"""Launch the bundled DragGAN browser demo.

This helper runs the web preflight first, then forwards the supported launch
flags to the installed ``draggan.web`` module.

Example:
  python scripts/launch_web_demo.py --device cuda --ip 0.0.0.0 --port 7860
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="cuda", help="Launch device passed to draggan.web")
    parser.add_argument("--share", action="store_true", help="Create a public Gradio link")
    parser.add_argument("-p", "--port", type=int, default=None, help="Server port")
    parser.add_argument("--ip", default=None, help="Server bind address")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip the bundled install check")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    preflight = root / "check_install.py"
    if not args.skip_preflight:
        rc = subprocess.run(
            [sys.executable, str(preflight), "--mode", "web"],
            check=False,
        )
        if rc.returncode != 0:
            return rc.returncode

    if args.device != "cuda":
        print(
            "[warn] The verified drag loop is CUDA-only in this snapshot; non-CUDA device values may fail when you click Drag it.",
            file=sys.stderr,
        )

    cmd = [sys.executable, "-m", "draggan.web", "--device", args.device]
    if args.share:
        cmd.append("--share")
    if args.port is not None:
        cmd.extend(["--port", str(args.port)])
    if args.ip is not None:
        cmd.extend(["--ip", args.ip])

    print("[launch]", " ".join(cmd), file=sys.stderr)
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
