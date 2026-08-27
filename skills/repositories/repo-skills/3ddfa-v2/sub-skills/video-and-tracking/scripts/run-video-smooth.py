#!/usr/bin/env python3
"""Wrapper for the original smoothed video demo CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_SCRIPTS = SCRIPT_DIR.parents[2] / "scripts"
sys.path.insert(0, str(ROOT_SCRIPTS))
from bootstrap_runtime import run_module_as_main  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=Path.cwd(), help="Path to the 3DDFA_V2 checkout")
    parser.add_argument("forwarded", nargs=argparse.REMAINDER, help="Arguments passed to demo_video_smooth.py after --")
    args = parser.parse_args()

    forwarded = args.forwarded
    if forwarded[:1] == ["--"]:
        forwarded = forwarded[1:]
    run_module_as_main("demo_video_smooth", forwarded, args.repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
