#!/usr/bin/env python3
"""Run safe OpenLLM environment diagnostics.

Examples:
  python check_installation.py
  python check_installation.py --check-gpu --json

This helper does not start OpenLLM servers, update repositories, deploy to cloud,
or delete caches. It only inspects the current Python environment and optional
read-only hardware state.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict


@dataclass
class Diagnostic:
    python: str
    import_ok: bool
    version: str | None
    cli_on_path: bool
    cli_help_ok: bool | None
    openllm_home: str | None
    do_not_track: str | None
    gpu_probe: dict[str, object] | None
    notes: list[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-gpu", action="store_true", help="Probe OpenLLM's local accelerator detector.")
    parser.add_argument("--check-cli-help", action="store_true", help="Run `openllm --help` as a safe console-script check.")
    parser.add_argument("--json", action="store_true", help="Render diagnostics as JSON.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    notes: list[str] = []
    version: str | None = None
    import_ok = False
    gpu_probe: dict[str, object] | None = None

    try:
        import openllm  # noqa: F401
        import_ok = True
    except Exception as exc:
        notes.append(f"import failed: {exc.__class__.__name__}: {exc}")

    try:
        version = metadata.version("openllm")
    except metadata.PackageNotFoundError:
        notes.append("distribution metadata for openllm not found")

    cli_path = shutil.which("openllm")
    cli_help_ok: bool | None = None
    if args.check_cli_help:
        if cli_path is not None:
            completed = subprocess.run([cli_path, "--help"], capture_output=True, text=True)
        else:
            completed = subprocess.run([sys.executable, "-m", "openllm", "--help"], capture_output=True, text=True)
            notes.append("openllm console script not found on PATH; checked `python -m openllm --help` instead")
        cli_help_ok = completed.returncode == 0
        if not cli_help_ok:
            notes.append((completed.stderr or completed.stdout or "openllm help check failed").strip())

    if args.check_gpu and import_ok:
        try:
            from openllm.accelerator_spec import get_local_machine_spec

            spec = get_local_machine_spec()
            gpu_probe = {
                "platform": spec.platform,
                "accelerator_count": len(spec.accelerators),
                "accelerators": [
                    {"model": accelerator.model, "memory_size": accelerator.memory_size}
                    for accelerator in spec.accelerators
                ],
            }
        except Exception as exc:
            gpu_probe = {"error": f"{exc.__class__.__name__}: {exc}"}
            notes.append("GPU probe failed")

    diag = Diagnostic(
        python=sys.executable,
        import_ok=import_ok,
        version=version,
        cli_on_path=cli_path is not None,
        cli_help_ok=cli_help_ok,
        openllm_home=os.environ.get("OPENLLM_HOME"),
        do_not_track=os.environ.get("BENTOML_DO_NOT_TRACK"),
        gpu_probe=gpu_probe,
        notes=notes,
    )

    if args.json:
        print(json.dumps(asdict(diag), indent=2, sort_keys=False))
    else:
        for key, value in asdict(diag).items():
            print(f"{key}: {value}")
    return 0 if import_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
