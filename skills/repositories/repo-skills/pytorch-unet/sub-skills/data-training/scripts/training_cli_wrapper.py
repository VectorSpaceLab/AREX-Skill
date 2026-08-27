#!/usr/bin/env python3
"""Preview or execute a Pytorch-UNet training command from a user checkout.

This bundled wrapper replaces direct reliance on a generated-time checkout. By
default it is a dry run: it validates that a caller-provided checkout contains
`train.py` and prints the exact command. Pass --execute only after the user has
approved training cost, W&B behavior, data access, checkpoint writes, and the
selected backend.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def emit(payload: Dict[str, Any], code: int = 0) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preview or execute a Pytorch-UNet train.py command")
    parser.add_argument("--repo-root", default=".", help="Pytorch-UNet checkout root containing train.py")
    parser.add_argument("--execute", action="store_true", help="Actually run train.py; default is dry-run preview")
    parser.add_argument(
        "--wandb-mode",
        choices=("unchanged", "offline", "disabled"),
        default="unchanged",
        help="Set WANDB_MODE before execution; dry runs only report the planned setting",
    )
    parser.add_argument("training_args", nargs=argparse.REMAINDER, help="Arguments for train.py after an optional -- separator")
    return parser.parse_args()


def clean_remainder(values: List[str]) -> List[str]:
    return values[1:] if values and values[0] == "--" else values


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    train_py = repo_root / "train.py"
    if not train_py.is_file():
        emit({"ok": False, "error": "train.py not found under repo root", "repo_root": str(repo_root)}, 2)

    forwarded = clean_remainder(args.training_args)
    command = [sys.executable, str(train_py), *forwarded]
    warnings = [
        "A real training run scans masks, initializes W&B, may use CUDA, and writes checkpoints.",
        "Run validate_dataset_layout.py and an environment/model smoke check before using --execute.",
        "Use --wandb-mode offline or --wandb-mode disabled when appropriate for the user's environment.",
    ]

    if not args.execute:
        emit(
            {
                "ok": True,
                "dry_run": True,
                "repo_root": str(repo_root),
                "command": command,
                "wandb_mode": args.wandb_mode,
                "warnings": warnings,
            }
        )

    env = os.environ.copy()
    if args.wandb_mode != "unchanged":
        env["WANDB_MODE"] = args.wandb_mode
    proc = subprocess.run(command, cwd=str(repo_root), env=env)
    emit(
        {
            "ok": proc.returncode == 0,
            "dry_run": False,
            "repo_root": str(repo_root),
            "command": command,
            "returncode": proc.returncode,
            "wandb_mode": args.wandb_mode,
            "warnings": warnings,
        },
        proc.returncode,
    )


if __name__ == "__main__":
    main()
