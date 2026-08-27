#!/usr/bin/env python3
"""Preview or execute a Pytorch-UNet prediction command from a user checkout.

This bundled wrapper replaces direct reliance on a generated-time checkout. By
default it is a dry run: it validates that a caller-provided checkout contains
`predict.py` and prints the exact command. Pass --execute only after the user has
approved reading checkpoint/image files and writing output masks.
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
    parser = argparse.ArgumentParser(description="Preview or execute a Pytorch-UNet predict.py command")
    parser.add_argument("--repo-root", default=".", help="Pytorch-UNet checkout root containing predict.py")
    parser.add_argument("--execute", action="store_true", help="Actually run predict.py; default is dry-run preview")
    parser.add_argument("prediction_args", nargs=argparse.REMAINDER, help="Arguments for predict.py after an optional -- separator")
    return parser.parse_args()


def clean_remainder(values: List[str]) -> List[str]:
    return values[1:] if values and values[0] == "--" else values


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    predict_py = repo_root / "predict.py"
    if not predict_py.is_file():
        emit({"ok": False, "error": "predict.py not found under repo root", "repo_root": str(repo_root)}, 2)

    forwarded = clean_remainder(args.prediction_args)
    command = [sys.executable, str(predict_py), *forwarded]
    warnings = [
        "A real prediction run reads checkpoint and image files and may write output masks.",
        "Run prediction_smoke.py first when you only need an import/checkpoint/mask-conversion sanity check.",
        "Avoid --viz in headless automation unless a display backend is configured.",
    ]

    if not args.execute:
        emit({"ok": True, "dry_run": True, "repo_root": str(repo_root), "command": command, "warnings": warnings})

    proc = subprocess.run(command, cwd=str(repo_root), env=os.environ.copy())
    emit(
        {
            "ok": proc.returncode == 0,
            "dry_run": False,
            "repo_root": str(repo_root),
            "command": command,
            "returncode": proc.returncode,
            "warnings": warnings,
        },
        proc.returncode,
    )


if __name__ == "__main__":
    main()
