#!/usr/bin/env python3
"""
Safe Axolotl environment checker for generated repo skill users.

This script checks package metadata, top-level import, the `axolotl` console
script, and lightweight help/schema commands. It never loads models, downloads
files, starts vLLM, runs preprocessing, or starts training.

Example:
  python scripts/check_axolotl_environment.py --json
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def run_command(argv: list[str], timeout: int) -> Check:
    try:
        proc = subprocess.run(
            argv,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return Check("command", False, f"not found: {argv[0]}")
    except subprocess.TimeoutExpired:
        return Check("command", False, f"timed out: {' '.join(argv)}")

    output = (proc.stdout or proc.stderr or "").strip().splitlines()
    detail = output[0] if output else f"exit {proc.returncode}"
    return Check("command", proc.returncode == 0, detail[:300])


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a local Axolotl install without running ML workloads.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--timeout", type=int, default=10, help="Seconds per CLI probe.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip axolotl CLI probes.")
    args = parser.parse_args()

    checks: list[Check] = []

    try:
        version = metadata.version("axolotl")
        checks.append(Check("distribution", True, f"axolotl {version}"))
    except metadata.PackageNotFoundError:
        checks.append(Check("distribution", False, "No axolotl distribution metadata in this Python environment."))

    try:
        module = importlib.import_module("axolotl")
        module_version = getattr(module, "__version__", "unknown")
        checks.append(Check("import", True, f"import axolotl ok; __version__={module_version}"))
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report any import failure.
        checks.append(Check("import", False, f"{type(exc).__name__}: {exc}"))

    executable = shutil.which("axolotl")
    checks.append(Check("console-script", executable is not None, executable or "axolotl not on PATH"))

    if executable and not args.skip_cli:
        help_check = run_command([executable, "--help"], args.timeout)
        checks.append(Check("axolotl --help", help_check.ok, help_check.detail))
        schema_check = run_command([executable, "config-schema", "--field", "base_model"], args.timeout)
        checks.append(Check("config-schema field", schema_check.ok, schema_check.detail))
        docs_check = run_command([executable, "agent-docs", "--list"], args.timeout)
        checks.append(Check("agent-docs list", docs_check.ok, docs_check.detail))

    payload: dict[str, Any] = {
        "python": sys.executable,
        "ok": all(check.ok for check in checks),
        "checks": [asdict(check) for check in checks],
        "notes": [
            "This is a shallow environment check only.",
            "Passing checks does not prove model download, tokenization, GPU kernels, vLLM, distributed launch, preprocessing, or training will work.",
        ],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for check in checks:
            status = "ok" if check.ok else "FAIL"
            print(f"[{status}] {check.name}: {check.detail}")
        for note in payload["notes"]:
            print(f"note: {note}")

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
