#!/usr/bin/env python3
"""Run a PointLLM launcher from the installed package.

PointLLM's historical launchers are package files rather than console entry
points and some use legacy sibling imports. This wrapper locates an allowed
launcher through the installed ``pointllm`` package and runs it without a
source-checkout path. It never downloads weights/data or starts a server unless
the selected launcher is explicitly asked to do so.

Example (from this generated skill directory):
  python scripts/run_installed_cli.py evaluator.py --help
"""
from __future__ import annotations

import argparse
import runpy
import sys
from importlib import import_module
from pathlib import Path

ALLOWED = {
    "PointLLM_chat.py",
    "chat_gradio.py",
    "eval_objaverse.py",
    "eval_modelnet_cls.py",
    "evaluator.py",
    "traditional_evaluator.py",
}


def main() -> int:
    # Do not let this wrapper consume `--help` intended for the selected
    # launcher. The launcher is parsed first; all remaining flags are forwarded.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("launcher", choices=sorted(ALLOWED))
    args, remainder = parser.parse_known_args()
    eval_dir = Path(import_module("pointllm.eval").__path__[0]).resolve()
    target = eval_dir / args.launcher
    if not target.is_file():
        parser.error(f"installed package does not contain {args.launcher}")
    sys.path.insert(0, str(eval_dir))
    sys.argv = [str(target), *remainder]
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
