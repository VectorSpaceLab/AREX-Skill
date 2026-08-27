#!/usr/bin/env python3
"""Read-only MatterGen package and backend smoke check.

Usage:
  python check_environment.py [--check-clis]

The helper imports lightweight public modules, reports distribution versions,
and probes CUDA/MPS without installing packages, downloading assets, or starting
training/generation/evaluation jobs.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import shutil
import subprocess
import sys
from typing import Iterable

DISTRIBUTIONS = (
    "mattergen",
    "torch",
    "torch_geometric",
    "pymatgen",
    "ase",
    "mattersim",
    "hydra-core",
    "pytorch-lightning",
)
MODULES = ("mattergen", "torch", "torch_geometric", "pymatgen", "ase")
CLIS = ("mattergen-generate", "mattergen-evaluate", "csv-to-dataset", "mattergen-train", "mattergen-finetune")


def _versions(names: Iterable[str]) -> tuple[dict[str, str], list[str]]:
    found: dict[str, str] = {}
    missing: list[str] = []
    for name in names:
        try:
            found[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(name)
    return found, missing


def _probe_modules(names: Iterable[str]) -> list[str]:
    failures: list[str] = []
    for name in names:
        try:
            importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - environment dependent
            failures.append(f"{name}: {type(exc).__name__}: {exc}")
    return failures


def _probe_torch() -> tuple[list[str], dict[str, object]]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - covered by module probe
        return [f"torch: {type(exc).__name__}: {exc}"], {}
    details: dict[str, object] = {
        "torch": torch.__version__,
        "compiled_cuda": torch.version.cuda,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_devices": int(torch.cuda.device_count()),
    }
    failures: list[str] = []
    if torch.cuda.is_available():
        try:
            details["cuda_device_0"] = torch.cuda.get_device_name(0)
            # Use a tiny allocation only; a busy device can still fail safely.
            sample = torch.ones(1, device="cuda")
            details["cuda_tensor_smoke"] = float((sample + 1).item()) == 2.0
        except Exception as exc:  # pragma: no cover - hardware dependent
            failures.append(f"CUDA tensor smoke: {type(exc).__name__}: {exc}")
    mps = getattr(torch.backends, "mps", None)
    details["mps_available"] = bool(mps is not None and mps.is_available())
    return failures, details


def _probe_clis() -> list[str]:
    failures: list[str] = []
    for cli in CLIS:
        path = shutil.which(cli)
        if path is None:
            failures.append(f"{cli}: executable not found")
            continue
        result = subprocess.run([path, "--help"], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            failures.append(f"{cli}: --help exited {result.returncode}: {result.stderr[-300:]}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-clis", action="store_true", help="also run each public console entry point with --help")
    args = parser.parse_args(argv)

    print(f"Python: {sys.version.split()[0]}")
    versions, missing = _versions(DISTRIBUTIONS)
    for name, value in versions.items():
        print(f"{name}: {value}")
    failures = [f"missing distribution: {name}" for name in missing]
    failures.extend(_probe_modules(MODULES))
    torch_failures, torch_details = _probe_torch()
    failures.extend(torch_failures)
    for key, value in torch_details.items():
        print(f"{key}: {value}")
    if args.check_clis:
        failures.extend(_probe_clis())
    if failures:
        print("Environment check: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Environment check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
