#!/usr/bin/env python3
"""Check whether OpenLLM is installed and optionally whether NVIDIA GPUs are visible.

Safe usage:
  python check_openllm_install.py
  python check_openllm_install.py --check-gpu

This helper only performs import/version/CLI-visibility checks and an optional
read-only hardware probe. It does not start models, download weights, update
model repositories, or mutate configuration.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import sys
from textwrap import indent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-gpu",
        action="store_true",
        help="Also probe the local machine with openllm.accelerator_spec.get_local_machine_spec().",
    )
    parser.add_argument(
        "--show-help",
        action="store_true",
        help="Print the root CLI help after import succeeds by shelling out to `openllm --help`.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        import openllm
        from openllm.accelerator_spec import get_local_machine_spec
    except Exception as exc:  # pragma: no cover - exercised manually
        print(f"OpenLLM import failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        version = metadata.version("openllm")
    except metadata.PackageNotFoundError:
        version = None

    print(f"distribution: openllm")
    print(f"version: {version or 'unknown'}")
    print(f"module: {openllm.__name__}")
    print(f"file: {getattr(openllm, '__file__', 'unknown')}")

    if args.check_gpu:
        try:
            spec = get_local_machine_spec()
        except Exception as exc:  # pragma: no cover - exercised manually
            print(f"GPU probe failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
            return 2
        print(f"platform: {spec.platform}")
        if spec.accelerators:
            print("accelerators:")
            for accelerator in spec.accelerators:
                print(indent(f"- {accelerator.model} ({accelerator.memory_size} GB)", "  "))
        else:
            print("accelerators: none detected")

    if args.show_help:
        import subprocess

        try:
            completed = subprocess.run(
                [sys.executable, "-m", "openllm", "--help"],
                check=True,
                capture_output=True,
                text=True,
            )
        except Exception as exc:  # pragma: no cover - exercised manually
            print(f"openllm --help failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
            return 3
        print(completed.stdout.rstrip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
