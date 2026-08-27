#!/usr/bin/env python
"""Inspect the active Logparser environment.

This script is a safe, read-only check for the bundled skill tree.
It prints the environment Python, key package versions, parser importability,
CUDA availability for NuLog, and host toolchain checks for SLCT/LogCluster.

Example:
    python scripts/check_install.py
    python scripts/check_install.py --json
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path



def _bootstrap_repo_root() -> None:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "setup.py").exists() and (candidate / "logparser").is_dir():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("Could not locate the repository root for Logparser")

def dist_version(name: str):
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def try_import(name: str):
    try:
        import_module(name)
        return {"ok": True}
    except Exception as exc:  # pragma: no cover - diagnostic helper
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    _bootstrap_repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON instead of human-readable text")
    args = parser.parse_args()

    report = {
        "python": {"executable": sys.executable, "version": sys.version},
        "distributions": {
            name: dist_version(name)
            for name in [
                "logparser3",
                "numpy",
                "pandas",
                "scipy",
                "scikit-learn",
                "nltk",
                "deap",
                "openai",
                "tiktoken",
                "keras-preprocessing",
                "torch",
                "torchvision",
                "matplotlib",
                "plotly",
                "tenacity",
            ]
        },
        "toolchain": {"gcc": shutil.which("gcc"), "perl": shutil.which("perl")},
        "imports": {},
        "cuda": {},
    }

    modules = [
        "logparser",
        "logparser.Drain",
        "logparser.AEL",
        "logparser.IPLoM",
        "logparser.LKE",
        "logparser.LFA",
        "logparser.LogSig",
        "logparser.LogCluster",
        "logparser.LenMa",
        "logparser.LogMine",
        "logparser.Spell",
        "logparser.Logram",
        "logparser.MoLFI",
        "logparser.NuLog",
        "logparser.Brain",
        "logparser.DivLog",
        "logparser.SLCT",
        "logparser.logmatch",
        "logparser.utils",
    ]
    for name in modules:
        report["imports"][name] = try_import(name)

    # SHISO needs the installed SHISO package directory on sys.path.
    try:
        import logparser  # type: ignore

        shiso_dir = Path(logparser.__file__).resolve().parent / "SHISO"
        sys.path.insert(0, str(shiso_dir))
        report["imports"]["logparser.SHISO"] = try_import("logparser.SHISO")
    except Exception as exc:  # pragma: no cover - diagnostic helper
        report["imports"]["logparser.SHISO"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    try:
        import torch

        report["cuda"] = {
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
        }
        if torch.cuda.is_available():
            report["cuda"]["device_name"] = torch.cuda.get_device_name(0)
            report["cuda"]["device_capability"] = list(torch.cuda.get_device_capability(0))
    except Exception as exc:  # pragma: no cover - diagnostic helper
        report["cuda"] = {"error": f"{type(exc).__name__}: {exc}"}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print("Logparser environment check")
    print("Python:", report["python"]["executable"])
    print("Version:", report["python"]["version"])
    print("\nDistributions:")
    for name, value in report["distributions"].items():
        print(f"  {name}: {value}")
    print("\nToolchain:")
    for name, value in report["toolchain"].items():
        print(f"  {name}: {value}")
    print("\nImports:")
    for name, status in report["imports"].items():
        if status.get("ok"):
            print(f"  {name}: ok")
        else:
            print(f"  {name}: FAIL {status.get('error')}")
    print("\nCUDA:")
    for key, value in report["cuda"].items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
