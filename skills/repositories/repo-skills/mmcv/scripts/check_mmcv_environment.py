#!/usr/bin/env python3
"""Run bundled MMCV skill diagnostics that are safe for the current package variant."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run self-contained MMCV skill helper scripts for media, transforms, "
            "CNN builders, and package/ops diagnostics."
        )
    )
    parser.add_argument(
        "--skip-media",
        action="store_true",
        help="skip media-processing smoke checks",
    )
    parser.add_argument(
        "--skip-transforms",
        action="store_true",
        help="skip data-transforms pipeline checks",
    )
    parser.add_argument(
        "--skip-cnn",
        action="store_true",
        help="skip cnn-model-building checks",
    )
    parser.add_argument(
        "--skip-full-ops",
        action="store_true",
        help="do not require compiled mmcv.ops; still run optional package diagnostic",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="require CUDA availability in the ops diagnostic",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable to use for helper scripts (default: current interpreter)",
    )
    return parser.parse_args()


def run(label: str, command: list[str]) -> tuple[str, int]:
    print(f"== {label} ==")
    print("$ " + " ".join(command))
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(completed.stdout.rstrip())
    print(f"exit: {completed.returncode}")
    return label, completed.returncode


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    python = args.python
    checks: list[tuple[str, list[str], bool]] = []

    if not args.skip_media:
        checks.append((
            "media-processing",
            [python, str(root / "sub-skills/media-processing/scripts/media_smoke_check.py")],
            True,
        ))
    if not args.skip_transforms:
        checks.append((
            "data-transforms",
            [python, str(root / "sub-skills/data-transforms/scripts/transform_pipeline_check.py")],
            True,
        ))
    if not args.skip_cnn:
        checks.append((
            "cnn-model-building",
            [python, str(root / "sub-skills/cnn-model-building/scripts/cnn_builder_smoke.py")],
            True,
        ))

    ops_command = [python, str(root / "sub-skills/ops-and-builds/scripts/check_mmcv_install.py")]
    if not args.skip_full_ops:
        ops_command.append("--require-ops")
    if args.require_cuda:
        ops_command.append("--require-cuda")
    checks.append(("ops-and-builds", ops_command, not args.skip_full_ops or args.require_cuda))

    failed_required: list[str] = []
    for label, command, required in checks:
        name, code = run(label, command)
        if code != 0 and required:
            failed_required.append(name)

    if failed_required:
        print("required checks failed: " + ", ".join(failed_required))
        return 1
    print("MMCV environment diagnostics completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
