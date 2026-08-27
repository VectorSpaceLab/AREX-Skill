#!/usr/bin/env python3
"""Check a MedSegDiff environment without downloading data or starting a run.

Use ``--repo-root`` when the source checkout is not importable yet. The helper
only imports public modules, reports dependency failures, and probes a tiny
CUDA allocation when requested. It never starts Visdom, training, sampling, or
network access.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any


MODULES = (
    "guided_diffusion.script_util",
    "guided_diffusion.gaussian_diffusion",
    "guided_diffusion.isicloader",
    "guided_diffusion.bratsloader",
    "guided_diffusion.custom_dataset_loader",
)
OPTIONAL_MODULES = ("visdom", "torchsummary", "nibabel", "blobfile")


def add_repo_root(repo_root: Path | None) -> None:
    if repo_root is None:
        return
    root = repo_root.expanduser().resolve()
    if not (root / "guided_diffusion").is_dir():
        raise SystemExit(f"error: --repo-root has no guided_diffusion directory: {root}")
    sys.path.insert(0, str(root))


def import_report(names: tuple[str, ...]) -> tuple[dict[str, str], dict[str, str]]:
    passed: dict[str, str] = {}
    failed: dict[str, str] = {}
    for name in names:
        try:
            module = importlib.import_module(name)
            passed[name] = getattr(module, "__file__", "imported") or "imported"
        except Exception as exc:  # dependency failures vary by platform/backend
            failed[name] = f"{type(exc).__name__}: {exc}"
    return passed, failed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, help="optional source checkout to add to sys.path")
    parser.add_argument("--cuda", action="store_true", help="probe one tiny CUDA allocation when available")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report")
    args = parser.parse_args()
    add_repo_root(args.repo_root)

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "required_imports": {},
        "optional_imports": {},
        "cuda": {"requested": bool(args.cuda)},
    }
    required_ok, required_failed = import_report(MODULES)
    optional_ok, optional_failed = import_report(OPTIONAL_MODULES)
    report["required_imports"] = {"passed": sorted(required_ok), "failed": required_failed}
    report["optional_imports"] = {"passed": sorted(optional_ok), "failed": optional_failed}

    try:
        import torch

        report["torch"] = {"version": torch.__version__, "cuda_runtime": torch.version.cuda}
        available = bool(torch.cuda.is_available())
        report["cuda"].update({"available": available, "device_count": torch.cuda.device_count()})
        if available:
            report["cuda"]["device_name"] = torch.cuda.get_device_name(0)
            report["cuda"]["capability"] = list(torch.cuda.get_device_capability(0))
            if args.cuda:
                try:
                    torch.empty((1,), device="cuda")
                    torch.cuda.synchronize()
                    report["cuda"]["allocation"] = "passed"
                except Exception as exc:
                    report["cuda"]["allocation"] = f"failed: {type(exc).__name__}: {exc}"
        elif args.cuda:
            report["cuda"]["allocation"] = "not-run: CUDA is unavailable"
    except Exception as exc:
        report["torch"] = {"error": f"{type(exc).__name__}: {exc}"}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"Required imports passed: {len(required_ok)}/{len(MODULES)}")
        for name, error in required_failed.items():
            print(f"  FAIL {name}: {error}")
        print(f"Optional imports passed: {len(optional_ok)}/{len(OPTIONAL_MODULES)}")
        cuda = report["cuda"]
        print(f"CUDA available: {cuda.get('available', 'unknown')}")
        if args.cuda:
            print(f"CUDA allocation: {cuda.get('allocation', 'not attempted')}")

    return 0 if not required_failed and "error" not in report.get("torch", {}) else 1


if __name__ == "__main__":
    raise SystemExit(main())
