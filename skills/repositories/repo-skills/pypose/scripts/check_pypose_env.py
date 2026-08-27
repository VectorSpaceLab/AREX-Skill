#!/usr/bin/env python3
"""Report PyPose, PyTorch, device, and optional sparse-backend readiness.

This read-only diagnostic uses only installed public packages. It performs no
network access, source-checkout imports, data downloads, or file writes. Run it
from any directory with the target environment active:

    python check_pypose_env.py

The exit status is nonzero only when the base PyPose/PyTorch import is broken.
Sparse readiness is reported separately because BAE/CUDA is optional for the
base package.
"""
from __future__ import annotations

import importlib.metadata as metadata
import json
import sys
from typing import Any


def distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "pypose": {"installed": distribution_version("pypose")},
        "torch": {"installed": distribution_version("torch")},
        "base_import": False,
        "sparse": {"available": False},
    }

    try:
        import torch
        import pypose as pp

        report["base_import"] = True
        report["pypose"]["runtime_version"] = pp.__version__
        report["torch"]["runtime_version"] = torch.__version__
        report["torch"]["cuda_build"] = torch.version.cuda
        report["torch"]["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            report["torch"]["cuda_devices"] = [
                torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
            ]

        try:
            import bae  # noqa: F401
            from pypose.autograd.function import psjac
            from pypose.optim.solver import PCG

            report["sparse"] = {
                "available": bool(torch.cuda.is_available()),
                "bae_version": distribution_version("bae"),
                "pcg": PCG.__module__ + "." + PCG.__name__,
                "psjac": psjac.__module__ + "." + psjac.__name__,
                "note": "CUDA and BAE are both required for sparse LM; CPU is not a substitute.",
            }
        except Exception as exc:
            report["sparse"] = {
                "available": False,
                "reason": f"{type(exc).__name__}: {exc}",
                "note": "Base PyPose remains usable without the optional BAE backend.",
            }
    except Exception as exc:
        report["base_import_error"] = f"{type(exc).__name__}: {exc}"

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["base_import"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
