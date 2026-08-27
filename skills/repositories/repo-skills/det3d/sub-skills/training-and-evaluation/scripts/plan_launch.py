#!/usr/bin/env python3
"""Validate a Det3D launch request and print a non-executing plan."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="Plan, but do not launch, a Det3D job")
    p.add_argument("mode", choices=["train", "test"])
    p.add_argument("config", type=Path)
    p.add_argument("--checkpoint", type=Path)
    p.add_argument("--work-dir", type=Path)
    p.add_argument("--gpus", type=int, default=1)
    p.add_argument("--launcher", default="none")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    errors = []
    if not args.config.is_file():
        errors.append("config does not exist")
    if args.mode == "test" and args.checkpoint is None:
        errors.append("test mode requires --checkpoint")
    if args.gpus < 1:
        errors.append("--gpus must be positive")
    result = {
        "mode": args.mode,
        "config": str(args.config),
        "checkpoint": str(args.checkpoint) if args.checkpoint else None,
        "work_dir": str(args.work_dir) if args.work_dir else None,
        "gpus": args.gpus,
        "launcher": args.launcher,
        "output": str(args.output) if args.output else None,
        "launch": False,
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
