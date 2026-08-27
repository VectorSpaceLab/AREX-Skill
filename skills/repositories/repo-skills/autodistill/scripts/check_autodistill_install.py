#!/usr/bin/env python3
"""Check a Python environment for safe core Autodistill use.

This root smoke script verifies the core distribution, imports key submodules,
checks ontology behavior, and reports the CLI executable if available. It does
not import model plugins, install packages, download weights, train models, use
GPU, or contact Roboflow.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-cli", action="store_true", help="Also run `autodistill --help` if the executable is on PATH.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        dist_version = version("autodistill")
    except PackageNotFoundError as exc:
        raise SystemExit("autodistill distribution metadata not found in this Python environment") from exc

    import autodistill
    import autodistill.classification
    import autodistill.core
    import autodistill.detection
    import autodistill.helpers
    import autodistill.registry
    import autodistill.text_classification
    import autodistill.utils
    from autodistill.detection import CaptionOntology

    ontology = CaptionOntology({"milk bottle": "bottle"})
    assert ontology.prompts() == ["milk bottle"]
    assert ontology.classes() == ["bottle"]
    try:
        CaptionOntology({})
    except ValueError:
        pass
    else:
        raise AssertionError("CaptionOntology({}) should raise ValueError")

    print(f"autodistill distribution version: {dist_version}")
    print(f"autodistill package version: {getattr(autodistill, '__version__', 'unknown')}")
    print("Core imports and CaptionOntology smoke passed.")

    executable = shutil.which("autodistill")
    if executable:
        print(f"CLI executable found on PATH: {executable}")
        if args.check_cli:
            proc = subprocess.run([executable, "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
            if proc.returncode != 0:
                raise SystemExit(f"autodistill --help failed: {proc.stderr.strip()}")
            if "--ontology" not in proc.stdout or "--base" not in proc.stdout:
                raise SystemExit("autodistill --help output did not include expected options")
            print("CLI help smoke passed.")
    else:
        print("CLI executable not found on PATH; package imports still passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
