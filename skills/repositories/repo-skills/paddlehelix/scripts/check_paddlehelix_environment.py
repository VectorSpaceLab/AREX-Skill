#!/usr/bin/env python3
"""Shared PaddleHelix import and optional dependency diagnostic.

The checker performs local imports and metadata checks only. It never downloads
models or data, starts training/inference, builds extensions, or mutates files.
Use --repo-root only when checking a local PaddleHelix source checkout.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
from pathlib import Path

OPTIONAL_DEPENDENCIES = {
    "numpy": "base array dependency for datasets and utilities",
    "pandas": "base table dependency declared by package metadata",
    "networkx": "base graph dependency declared by package metadata",
    "sklearn": "legacy import name; install scikit-learn in modern environments",
    "paddle": "required for model_zoo classes, training, and inference",
    "pgl": "required for graph dataloaders, many featurizers, and GNN workflows",
    "rdkit": "required for scaffold splitting and compound graph utilities",
    "openbabel": "commonly required by docking/conversion workflows",
}

MODULE_CHECKS = [
    "pahelix",
]

OPTIONAL_MODULE_CHECKS = [
    "pahelix.utils.data_utils",
    "pahelix.utils.protein_tools",
    "pahelix.datasets.inmemory_dataset",
    "pahelix.utils.splitters",
    "pahelix.utils.compound_tools",
    "pahelix.featurizers.gem_featurizer",
    "pahelix.model_zoo.pretrain_gnns_model",
    "pahelix.model_zoo.protein_sequence_model",
]


def add_repo_root(repo_root: str | None) -> Path | None:
    if not repo_root:
        return None
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"--repo-root does not exist: {root}")
    if not (root / "pahelix").is_dir():
        raise SystemExit(f"--repo-root must contain a pahelix/ package: {root}")
    text = str(root)
    if text not in sys.path:
        sys.path.insert(0, text)
    return root


def module_status(module_name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        return {
            "module": module_name,
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "missing": getattr(exc, "name", None),
        }
    return {
        "module": module_name,
        "ok": True,
        "file": str(getattr(module, "__file__", "")) or None,
    }


def dependency_status(module_name: str, purpose: str) -> dict[str, object]:
    found = importlib.util.find_spec(module_name) is not None
    status = {"module": module_name, "ok": found, "purpose": purpose}
    if not found:
        if module_name == "sklearn":
            status["hint"] = "Install scikit-learn; avoid relying on deprecated pip package name sklearn unless a legacy setup path requires it."
        elif module_name == "paddle":
            status["hint"] = "Install a PaddlePaddle CPU/GPU build compatible with the selected hardware before model training or inference."
        elif module_name == "pgl":
            status["hint"] = "Install a PGL version compatible with the selected PaddlePaddle build before graph dataloaders or GNN apps."
        elif module_name == "rdkit":
            status["hint"] = "Install RDKit before scaffold splitting, molecule parsing, or chemistry feature utilities."
        elif module_name == "openbabel":
            status["hint"] = "Install OpenBabel only for workflows that explicitly need conversion/docking preparation."
    return status


def distribution_status() -> dict[str, object]:
    for name in ("paddlehelix", "PaddleHelix"):
        try:
            dist = importlib.metadata.distribution(name)
        except importlib.metadata.PackageNotFoundError:
            continue
        requirements = dist.requires or []
        return {"ok": True, "name": dist.metadata.get("Name", name), "version": dist.version, "requires": requirements}
    return {"ok": False, "hint": "Distribution metadata not found; use --repo-root for source-layout checks or install paddlehelix."}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Optional local PaddleHelix checkout containing pahelix/.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text report.")
    parser.add_argument("--optional-modules", action="store_true", help="Attempt optional pahelix modules that may require paddle/pgl/rdkit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    add_repo_root(args.repo_root)

    report = {
        "distribution": distribution_status(),
        "required_modules": [module_status(name) for name in MODULE_CHECKS],
        "optional_dependencies": [dependency_status(name, purpose) for name, purpose in OPTIONAL_DEPENDENCIES.items()],
        "optional_modules": [],
    }
    if args.optional_modules:
        report["optional_modules"] = [module_status(name) for name in OPTIONAL_MODULE_CHECKS]

    required_ok = all(item["ok"] for item in report["required_modules"])

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        dist = report["distribution"]
        if dist["ok"]:
            print(f"distribution: {dist['name']} {dist['version']}")
        else:
            print(f"distribution: not found ({dist['hint']})")
        print("\nrequired modules")
        for item in report["required_modules"]:
            marker = "OK" if item["ok"] else "ERROR"
            detail = item.get("file") or item.get("error")
            print(f"[{marker}] {item['module']}: {detail}")
        print("\noptional dependencies")
        for item in report["optional_dependencies"]:
            marker = "OK" if item["ok"] else "MISSING"
            print(f"[{marker}] {item['module']}: {item['purpose']}")
            if not item["ok"] and "hint" in item:
                print(f"  hint: {item['hint']}")
        if args.optional_modules:
            print("\noptional pahelix modules")
            for item in report["optional_modules"]:
                marker = "OK" if item["ok"] else "SKIP"
                detail = item.get("file") or item.get("error")
                print(f"[{marker}] {item['module']}: {detail}")

    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
