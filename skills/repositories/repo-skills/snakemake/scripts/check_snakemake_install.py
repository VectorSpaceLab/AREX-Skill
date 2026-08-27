#!/usr/bin/env python3
"""Check that a Snakemake CLI and Python module are usable.

This helper creates no workflow files. It runs safe help/import probes and prints
plain-text diagnostics suitable for agents deciding whether to route to CLI or
Python API guidance.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Sequence


@dataclass
class ProbeResult:
    name: str
    ok: bool
    detail: str


def run_command(args: Sequence[str], timeout: int) -> ProbeResult:
    label = " ".join(args)
    try:
        completed = subprocess.run(
            list(args),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return ProbeResult(label, False, "executable not found")
    except subprocess.TimeoutExpired:
        return ProbeResult(label, False, f"timed out after {timeout}s")

    output = (completed.stdout + completed.stderr).strip().splitlines()
    first_lines = "\n".join(output[:8])
    return ProbeResult(label, completed.returncode == 0, first_lines or f"exit {completed.returncode}")


def import_probe() -> ProbeResult:
    try:
        import snakemake  # noqa: F401

        version = metadata.version("snakemake")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return ProbeResult("import snakemake", False, f"{type(exc).__name__}: {exc}")
    return ProbeResult("import snakemake", True, f"snakemake {version}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", default="snakemake", help="Snakemake executable to probe")
    parser.add_argument("--python", default=sys.executable, help="Python executable to probe with -m snakemake")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout per help command")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain text")
    args = parser.parse_args()

    probes = [
        import_probe(),
        run_command([args.python, "-m", "snakemake", "--help"], args.timeout),
    ]

    command_path = shutil.which(args.command) if args.command == "snakemake" else args.command
    if command_path:
        probes.append(run_command([args.command, "--help"], args.timeout))
    else:
        probes.append(ProbeResult(args.command, False, "executable not found on PATH"))

    if args.json:
        print(json.dumps([asdict(probe) for probe in probes], indent=2))
    else:
        for probe in probes:
            status = "PASS" if probe.ok else "FAIL"
            print(f"[{status}] {probe.name}")
            print(probe.detail)
            print()

    return 0 if all(probe.ok for probe in probes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
