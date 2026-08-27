#!/usr/bin/env python
"""Print a compact DeepChem environment and optional dependency report."""

import importlib
import importlib.metadata as metadata
import json
import platform

OPTIONAL_MODULES = [
    "numpy",
    "pandas",
    "scipy",
    "sklearn",
    "rdkit",
    "torch",
    "tensorflow",
    "jax",
    "dgl",
    "dgllife",
    "pytorch_lightning",
    "mdtraj",
    "vina",
    "openmm",
    "pdbfixer",
    "pymatgen",
    "matminer",
    "dqc",
]


def module_status(name):
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # ImportError and optional backend import failures
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    if version is None:
        try:
            version = metadata.version(name.replace("_", "-"))
        except metadata.PackageNotFoundError:
            version = "unknown"
    return {"ok": True, "version": version}


def main():
    report = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "deepchem_distribution": None,
        "deepchem_import": module_status("deepchem"),
        "modules": {name: module_status(name) for name in OPTIONAL_MODULES},
    }
    try:
        report["deepchem_distribution"] = metadata.version("deepchem")
    except metadata.PackageNotFoundError:
        report["deepchem_distribution"] = None
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
