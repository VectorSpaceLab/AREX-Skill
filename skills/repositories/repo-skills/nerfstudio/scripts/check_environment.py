#!/usr/bin/env python3
"""Read-only Nerfstudio environment diagnostic.

This helper checks package importability, selected console entry points, optional
external binaries, and PyTorch CUDA visibility. It never downloads data, starts a
viewer, launches training, or writes outside stdout.

Example:
    python check_environment.py --require-cuda --check-cli
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
from importlib import metadata


def _entry_points():
    eps = metadata.entry_points()
    if hasattr(eps, "select"):
        return eps.select(group="console_scripts")
    return eps.get("console_scripts", [])


def _run_help(command: str, timeout: int) -> tuple[bool, str]:
    path = shutil.which(command)
    if path is None:
        return False, f"{command}: not found on PATH"
    try:
        proc = subprocess.run([path, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"{command}: --help timed out after {timeout}s"
    if proc.returncode != 0:
        return False, f"{command}: --help exited {proc.returncode}: {proc.stdout[-500:]}"
    first_line = proc.stdout.splitlines()[0] if proc.stdout.splitlines() else "help printed"
    return True, f"{command}: {first_line}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a Nerfstudio installation without running training or downloads.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if torch CUDA is unavailable.")
    parser.add_argument("--check-cli", action="store_true", help="Run --help for common ns-* commands.")
    parser.add_argument("--help-timeout", type=int, default=20, help="Seconds per CLI --help check.")
    args = parser.parse_args()

    failures: list[str] = []

    try:
        version = metadata.version("nerfstudio")
        import nerfstudio  # noqa: F401
        print(f"nerfstudio distribution: {version}")
    except Exception as exc:  # pragma: no cover - diagnostic output
        failures.append(f"nerfstudio import/metadata failed: {exc}")

    for module in [
        "nerfstudio.configs.method_configs",
        "nerfstudio.configs.dataparser_configs",
        "nerfstudio.scripts.train",
        "nerfstudio.scripts.process_data",
        "nerfstudio.scripts.eval",
        "nerfstudio.scripts.render",
        "nerfstudio.scripts.exporter",
        "nerfstudio.scripts.viewer.run_viewer",
        "nerfstudio.plugins.registry",
    ]:
        try:
            importlib.import_module(module)
            print(f"import ok: {module}")
        except Exception as exc:  # pragma: no cover - diagnostic output
            failures.append(f"import failed: {module}: {exc}")

    try:
        import torch

        print(f"torch: {torch.__version__}; torch CUDA runtime: {torch.version.cuda}")
        cuda_ok = bool(torch.cuda.is_available())
        print(f"torch.cuda.is_available: {cuda_ok}; device_count: {torch.cuda.device_count()}")
        if cuda_ok:
            print(f"cuda device 0: {torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)}")
            torch.empty((1,), device="cuda")
        elif args.require_cuda:
            failures.append("CUDA was required but torch.cuda.is_available() is false.")
    except Exception as exc:  # pragma: no cover - diagnostic output
        failures.append(f"torch/CUDA check failed: {exc}")

    for binary in ["ffmpeg", "colmap"]:
        path = shutil.which(binary)
        print(f"external binary {binary}: {path or 'not found'}")

    ep_map = {ep.name: ep.value for ep in _entry_points() if ep.name.startswith("ns-")}
    print("ns entry points:")
    for name in sorted(ep_map):
        print(f"  {name}: {ep_map[name]}")

    if args.check_cli:
        for command in ["ns-train", "ns-process-data", "ns-eval", "ns-render", "ns-export", "ns-viewer", "ns-download-data"]:
            ok, message = _run_help(command, args.help_timeout)
            print(message)
            if not ok:
                failures.append(message)

    if failures:
        print("\nFAILURES:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Nerfstudio environment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
