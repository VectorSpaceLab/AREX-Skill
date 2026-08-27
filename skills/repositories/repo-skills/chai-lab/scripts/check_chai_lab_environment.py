#!/usr/bin/env python3
"""Lightweight Chai Lab environment check.

This script imports Chai Lab, optionally checks the CLI, reports PyTorch/CUDA
visibility, and prints CHAI_DOWNLOADS_DIR status. It does not run inference,
download model weights, or contact MSA/template servers.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class CheckResult:
    ok: bool
    python: str
    chai_import: bool
    chai_version: str | None
    run_inference_import: bool
    cli_path: str | None
    cli_help_ok: bool | None
    torch_import: bool
    torch_version: str | None
    cuda_available: bool | None
    cuda_device_count: int | None
    cuda_devices: list[str]
    downloads_dir_set: bool
    downloads_dir: str | None
    errors: list[str]


def run_cli_help(command: str) -> bool:
    try:
        completed = subprocess.run(
            [command, "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
    except Exception:
        return False
    return completed.returncode == 0


def collect(check_cli: bool, require_cuda: bool) -> CheckResult:
    errors: list[str] = []
    chai_import = False
    chai_version: str | None = None
    run_inference_import = False

    try:
        chai_lab = importlib.import_module("chai_lab")
        chai_import = True
        chai_version = getattr(chai_lab, "__version__", None)
    except Exception as exc:
        errors.append(f"chai_lab import failed: {exc}")

    try:
        module = importlib.import_module("chai_lab.chai1")
        getattr(module, "run_inference")
        run_inference_import = True
    except Exception as exc:
        errors.append(f"chai_lab.chai1.run_inference import failed: {exc}")

    cli_path = shutil.which("chai-lab")
    cli_help_ok: bool | None = None
    if check_cli:
        if cli_path is None:
            cli_help_ok = False
            errors.append("chai-lab CLI was not found on PATH")
        else:
            cli_help_ok = run_cli_help(cli_path)
            if not cli_help_ok:
                errors.append("chai-lab --help did not exit successfully")

    torch_import = False
    torch_version: str | None = None
    cuda_available: bool | None = None
    cuda_device_count: int | None = None
    cuda_devices: list[str] = []
    try:
        torch = importlib.import_module("torch")
        torch_import = True
        torch_version = getattr(torch, "__version__", None)
        cuda_available = bool(torch.cuda.is_available())
        cuda_device_count = int(torch.cuda.device_count())
        if cuda_available:
            cuda_devices = [torch.cuda.get_device_name(i) for i in range(cuda_device_count)]
    except Exception as exc:
        errors.append(f"torch inspection failed: {exc}")

    if require_cuda and not cuda_available:
        errors.append("CUDA was required but torch.cuda.is_available() is false")

    downloads_dir = os.environ.get("CHAI_DOWNLOADS_DIR")
    ok = chai_import and run_inference_import and (cli_help_ok is not False) and not (require_cuda and not cuda_available)
    return CheckResult(
        ok=ok,
        python=sys.executable,
        chai_import=chai_import,
        chai_version=chai_version,
        run_inference_import=run_inference_import,
        cli_path=cli_path,
        cli_help_ok=cli_help_ok,
        torch_import=torch_import,
        torch_version=torch_version,
        cuda_available=cuda_available,
        cuda_device_count=cuda_device_count,
        cuda_devices=cuda_devices,
        downloads_dir_set=downloads_dir is not None,
        downloads_dir=downloads_dir,
        errors=errors,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Chai Lab import, CLI, CUDA visibility, and download-cache configuration without running inference.")
    parser.add_argument("--check-cli", action="store_true", help="Run chai-lab --help if the CLI is on PATH.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if PyTorch does not report CUDA availability.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text report.")
    args = parser.parse_args()

    result = collect(check_cli=args.check_cli, require_cuda=args.require_cuda)
    data: dict[str, Any] = asdict(result)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        for key, value in data.items():
            print(f"{key}: {value}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
