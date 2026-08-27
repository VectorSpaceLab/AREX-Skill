#!/usr/bin/env python3
"""Read-only BindCraft environment and asset diagnostic.

This helper reports Python distributions, CUDA/JAX device visibility, and
optional AF2/DSSP/DAlphaBall paths. It never installs packages, changes files,
or starts BindCraft.
"""
from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import os
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check-assets", action="store_true", help="check supplied external asset paths")
    p.add_argument("--af-params-dir", type=Path)
    p.add_argument("--dssp-path", type=Path)
    p.add_argument("--dalphaball-path", type=Path)
    return p


def distribution(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "missing"


def main() -> int:
    args = parser().parse_args()
    print(f"python={os.sys.version.split()[0]}")
    print("distributions:")
    for name in ("jax", "jaxlib", "colabdesign", "pyrosetta", "biopython", "numpy", "scipy", "pandas"):
        print(f"  {name}={distribution(name)}")
    print("imports:")
    for module in ("jax", "colabdesign", "pyrosetta", "Bio", "scipy"):
        print(f"  {module}={'present' if importlib.util.find_spec(module) else 'missing'}")

    status = 0
    try:
        import jax
        devices = jax.devices()
        print(f"jax_devices={devices}")
        print(f"cuda_devices={sum(getattr(device, 'platform', None) == 'gpu' for device in devices)}")
    except Exception as exc:
        print(f"jax_probe=error: {type(exc).__name__}: {exc}")
        status = 2

    if args.check_assets:
        for label, value in (("af_params_dir", args.af_params_dir), ("dssp_path", args.dssp_path), ("dalphaball_path", args.dalphaball_path)):
            if value is None:
                print(f"{label}=not supplied")
                continue
            exists = value.exists()
            executable = os.access(value, os.X_OK)
            print(f"{label}={value} exists={exists} executable={executable}")
            if not exists:
                status = max(status, 3)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
