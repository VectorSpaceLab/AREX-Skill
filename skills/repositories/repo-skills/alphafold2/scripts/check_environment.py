#!/usr/bin/env python3
"""Read-only package, dependency, and optional CUDA inspection.

Run from any working directory after installing alphafold2-pytorch. The helper
never installs packages, downloads weights, or changes files.
"""
from __future__ import annotations

import importlib
from importlib import metadata

DISTRIBUTIONS = (
    "alphafold2-pytorch",
    "torch",
    "pytorch3d",
    "invariant-point-attention",
    "En-transformer",
    "sidechainnet",
    "openmm",
    "mdtraj",
    "ProDy",
    "mp-nerf",
    "transformers",
)
MODULES = (
    "alphafold2_pytorch",
    "torch",
    "pytorch3d",
    "invariant_point_attention",
    "sidechainnet",
    "openmm",
    "mdtraj",
    "prody",
    "mp_nerf",
    "transformers",
)


def main() -> int:
    print("DisCo alphafold2 environment inspection (read-only)")
    for name in DISTRIBUTIONS:
        try:
            print(f"distribution {name}={metadata.version(name)}")
        except metadata.PackageNotFoundError:
            print(f"distribution {name}=MISSING")
    for name in MODULES:
        try:
            module = importlib.import_module(name)
            print(f"module {name}=OK")
            if name == "torch":
                print(f"torch.version={module.__version__}")
                print(f"torch.cuda_available={module.cuda.is_available()}")
                print(f"torch.cuda_version={module.version.cuda}")
        except Exception as exc:
            print(f"module {name}=ERROR {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
