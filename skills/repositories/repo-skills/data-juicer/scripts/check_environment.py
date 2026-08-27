#!/usr/bin/env python3
"""Safe Data-Juicer environment smoke check.

Checks:
- import `data_juicer`
- `data_juicer.core` public surface
- CLI help for the installed console scripts
- optional Ray startup when requested
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from typing import Iterable


def run_help(command: str) -> tuple[bool, str]:
    if shutil.which(command) is None:
        return False, f"missing command: {command}"
    proc = subprocess.run([command, "--help"], capture_output=True, text=True)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "unknown failure"
        return False, f"{command} --help failed: {detail}"
    return True, f"{command} --help ok"


def print_lines(lines: Iterable[str]) -> None:
    for line in lines:
        print(line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-ray", action="store_true", help="Also attempt a tiny local Ray init smoke test.")
    args = parser.parse_args()

    failures: list[str] = []

    try:
        import data_juicer
        import data_juicer.core as core

        print(f"data_juicer={getattr(data_juicer, '__version__', 'unknown')}")
        print(f"core_exports={','.join(core.__all__)}")
    except Exception as exc:
        failures.append(f"import failed: {exc}")

    for command in ("dj-process", "dj-analyze", "dj-install", "dj-mcp"):
        ok, message = run_help(command)
        print(message)
        if not ok:
            failures.append(message)

    if args.check_ray:
        try:
            import ray

            ray.init(num_cpus=1, include_dashboard=False, ignore_reinit_error=True)
            print(f"ray={ray.__version__}")
            print(f"ray_resources={ray.cluster_resources()}")
            print(f"ray_initialized={ray.is_initialized()}")
            ray.shutdown()
        except Exception as exc:
            failures.append(f"ray smoke failed: {exc}")

    if failures:
        print_lines([f"FAIL: {item}" for item in failures])
        return 1

    print("environment ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
