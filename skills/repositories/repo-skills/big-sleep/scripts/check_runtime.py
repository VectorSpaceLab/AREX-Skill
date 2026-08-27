#!/usr/bin/env python3
"""Check the installed Big Sleep runtime.

This helper is safe by default: it prints package/version/signature information
and verifies that CUDA is visible to torch. Pass --check-cli to also run
`dream --help` as a parser/entry-point smoke test.
"""

from __future__ import annotations

import argparse
import inspect
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path


def _fail(message: str, exit_code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def _check_torch() -> None:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        _fail(f"unable to import torch: {exc}")

    print(f"torch: {torch.__version__}")
    print(f"torch.cuda: {torch.version.cuda}")
    print(f"torch.cuda.is_available: {torch.cuda.is_available()}")
    print(f"torch.cuda.device_count: {torch.cuda.device_count()}")

    if not torch.cuda.is_available():
        _fail("CUDA is not available inside the current environment")

    print(f"torch.cuda.device_name[0]: {torch.cuda.get_device_name(0)}")
    print(f"torch.cuda.capability[0]: {torch.cuda.get_device_capability(0)}")
    torch.empty((1,), device="cuda")
    print("torch.cuda smoke: ok")


def _check_big_sleep() -> None:
    try:
        import big_sleep
        from big_sleep import BigSleep, Imagine
        from big_sleep.cli import train
    except Exception as exc:  # pragma: no cover - diagnostic path
        _fail(f"unable to import big_sleep: {exc}")

    print(f"big-sleep version: {version('big-sleep')}")
    print(f"big_sleep module: {Path(big_sleep.__file__).resolve()}")
    print(f"Imagine signature: {inspect.signature(Imagine)}")
    print(f"BigSleep signature: {inspect.signature(BigSleep)}")
    print(f"train signature: {inspect.signature(train)}")


def _check_cli() -> None:
    try:
        result = subprocess.run(
            ["dream", "--help"],
            check=False,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:  # pragma: no cover - diagnostic path
        _fail(f"dream command not found: {exc}")

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown CLI failure"
        _fail(f"dream --help failed: {stderr}")

    first_line = (result.stdout or "").splitlines()[0] if result.stdout else "dream --help: ok"
    print(first_line)
    print("dream --help: ok")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-cli",
        action="store_true",
        help="also run `dream --help` as a CLI smoke check",
    )
    args = parser.parse_args(argv)

    _check_torch()
    _check_big_sleep()
    if args.check_cli:
        _check_cli()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
