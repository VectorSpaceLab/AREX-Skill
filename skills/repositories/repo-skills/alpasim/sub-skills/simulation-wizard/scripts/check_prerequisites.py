#!/usr/bin/env python3
"""Safe, read-only AlpaSim wizard prerequisite probe.

This helper never installs packages, contacts Hugging Face, starts containers,
or submits scheduler jobs. It reports executable presence and environment
signals so a user can decide which documented setup step is still required.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Probe:
    name: str
    ok: bool
    detail: str


def command_probe(name: str, *args: str) -> Probe:
    executable = shutil.which(name)
    if not executable:
        return Probe(name, False, "not found on PATH")
    try:
        result = subprocess.run(
            [executable, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return Probe(name, False, f"could not run: {exc}")
    output = (result.stdout or result.stderr).strip().splitlines()
    detail = output[0] if output else f"exit={result.returncode}"
    return Probe(name, result.returncode == 0, detail)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--imports",
        action="store_true",
        help="also probe lightweight Python module discovery",
    )
    args = parser.parse_args()

    probes = [
        command_probe("uv", "--version"),
        command_probe("docker", "compose", "version"),
        command_probe("nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"),
        command_probe("cargo", "--version"),
    ]
    print("AlpaSim wizard read-only prerequisite probe")
    for probe in probes:
        status = "OK" if probe.ok else "MISSING/UNVERIFIED"
        print(f"[{status}] {probe.name}: {probe.detail}")

    print(f"[INFO] HF_TOKEN={'set' if os.environ.get('HF_TOKEN') else 'not set'} (value not shown)")
    print(f"[INFO] HF_HOME={os.environ.get('HF_HOME', '~/.cache/huggingface')}")

    if args.imports:
        for module in ("hydra", "omegaconf", "polars", "huggingface_hub"):
            found = importlib.util.find_spec(module) is not None
            print(f"[{'OK' if found else 'MISSING'}] python:{module}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
