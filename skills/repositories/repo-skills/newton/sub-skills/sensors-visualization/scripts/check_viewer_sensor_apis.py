#!/usr/bin/env python3
"""Inspect Newton sensor/viewer APIs and example CLI availability."""

from __future__ import annotations

import argparse
import importlib
import inspect
import subprocess
import sys

TARGETS = [
    ("newton.sensors", "SensorContact"),
    ("newton.sensors", "SensorFrameTransform"),
    ("newton.sensors", "SensorIMU"),
    ("newton.sensors", "SensorTiledCamera"),
    ("newton.viewer", "ViewerNull"),
    ("newton.viewer", "ViewerFile"),
    ("newton.viewer", "ViewerUSD"),
    ("newton.viewer", "ViewerGL"),
    ("newton.viewer", "ViewerRTX"),
    ("newton.viewer", "ViewerRerun"),
    ("newton.viewer", "ViewerViser"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check public Newton sensor/viewer APIs and example CLI.")
    parser.add_argument("--skip-cli", action="store_true", help="Do not invoke python -m newton.examples --list.")
    parser.add_argument("--limit", type=int, default=10, help="Number of example names to print when CLI is checked.")
    args = parser.parse_args()

    try:
        import newton
    except ModuleNotFoundError:
        print("ERROR: Newton is not importable. Install the base package first.")
        return 2

    print(f"newton={getattr(newton, '__version__', 'unknown')}")
    for mod_name, attr in TARGETS:
        try:
            mod = importlib.import_module(mod_name)
            obj = getattr(mod, attr)
            print(f"{mod_name}.{attr}{inspect.signature(obj)}")
        except Exception as exc:  # noqa: BLE001
            print(f"{mod_name}.{attr}: unavailable ({type(exc).__name__}: {exc})")

    try:
        viewer = newton.viewer.ViewerNull(num_frames=1)
        print(f"ViewerNull.is_running={viewer.is_running()}")
        viewer.close()
    except Exception as exc:  # noqa: BLE001
        print(f"ViewerNull smoke failed: {type(exc).__name__}: {exc}")
        return 3

    if not args.skip_cli:
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "newton.examples", "--list"],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=20,
            )
        except subprocess.TimeoutExpired:
            print("example CLI list timed out")
            return 4
        lines = completed.stdout.splitlines()
        for line in lines[: max(args.limit + 1, 1)]:
            print("example-cli: " + line)
        if completed.returncode != 0:
            print("example CLI returned non-zero; install newton[examples] if example dependencies are required")
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
