#!/usr/bin/env python3
"""Safe Boltz environment preflight helper.

This script checks package metadata, importability, CLI availability, and optional
PyTorch backend facts. It does not download models, call MSA servers, start
services, or run prediction/training/evaluation workloads.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import shutil
import subprocess
import sys


def run(command: list[str], timeout: int = 20) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", exc.stderr or "timeout"
    return completed.returncode, completed.stdout, completed.stderr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a Boltz Python environment safely.")
    parser.add_argument("--skip-cli", action="store_true", help="Do not run boltz --help checks")
    parser.add_argument("--check-torch", action="store_true", help="Print PyTorch CPU/CUDA facts if torch imports")
    args = parser.parse_args(argv)

    status = 0
    try:
        version = metadata.version("boltz")
        print(f"boltz distribution: {version}")
    except metadata.PackageNotFoundError:
        print("ERROR: boltz distribution metadata not found")
        status = 1

    try:
        import boltz  # noqa: F401

        print("boltz import: ok")
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: boltz import failed: {exc}")
        status = 1

    if args.skip_cli:
        print("boltz CLI: skipped")
    else:
        executable = shutil.which("boltz")
        if executable:
            print("boltz CLI: found")
        else:
            print("WARN: boltz CLI not found on PATH")
            status = max(status, 1)

        if executable:
            for command in (["boltz", "--help"], ["boltz", "predict", "--help"]):
                code, stdout, stderr = run(command)
                label = " ".join(command)
                if code == 0:
                    first = stdout.splitlines()[0] if stdout.splitlines() else "ok"
                    print(f"{label}: ok ({first})")
                else:
                    print(f"ERROR: {label} failed with {code}: {stderr.strip()}")
                    status = 1

    if args.check_torch:
        try:
            import torch

            print(f"torch: {torch.__version__}")
            print(f"torch cuda version: {torch.version.cuda}")
            print(f"torch cuda available: {torch.cuda.is_available()}")
            print(f"torch cuda devices: {torch.cuda.device_count()}")
            if torch.cuda.is_available():
                print(f"torch cuda device 0: {torch.cuda.get_device_name(0)}")
        except Exception as exc:  # noqa: BLE001
            print(f"WARN: torch check failed: {exc}")

    return status


if __name__ == "__main__":
    raise SystemExit(main())
