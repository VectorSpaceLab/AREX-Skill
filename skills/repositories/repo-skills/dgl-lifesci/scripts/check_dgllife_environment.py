#!/usr/bin/env python3
"""Safe environment checker for DGL-LifeSci/dgllife workflows."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from typing import Any


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        return {
            "ok": True,
            "version": getattr(module, "__version__", None),
            "file": getattr(module, "__file__", None),
        }
    except Exception as exc:  # noqa: BLE001 - diagnostics should report any import failure.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def signature_status(qualified_name: str) -> dict[str, Any]:
    module_name, attr_name = qualified_name.rsplit(".", 1)
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, attr_name)
        return {"ok": True, "signature": str(inspect.signature(obj))}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check imports and key signatures for DGL-LifeSci workflows.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument(
        "--include-signatures",
        action="store_true",
        help="Inspect representative dgllife signatures after imports succeed.",
    )
    args = parser.parse_args()

    modules = ["dgllife", "dgl", "torch", "rdkit", "numpy", "scipy", "pandas", "sklearn"]
    report = {
        "python": sys.version,
        "imports": {name: import_status(name) for name in modules},
        "signatures": {},
    }

    if args.include_signatures and report["imports"].get("dgllife", {}).get("ok"):
        targets = [
            "dgllife.utils.smiles_to_bigraph",
            "dgllife.utils.CanonicalAtomFeaturizer",
            "dgllife.data.MoleculeCSVDataset",
            "dgllife.model.GCNPredictor",
            "dgllife.model.load_pretrained",
        ]
        report["signatures"] = {target: signature_status(target) for target in targets}

    failed = [name for name, result in report["imports"].items() if not result.get("ok")]
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {sys.version.split()[0]}")
        for name, result in report["imports"].items():
            if result.get("ok"):
                version = result.get("version") or "version unknown"
                print(f"OK   {name}: {version}")
            else:
                print(f"FAIL {name}: {result.get('error')}")
        if report["signatures"]:
            print("\nRepresentative signatures:")
            for name, result in report["signatures"].items():
                if result.get("ok"):
                    print(f"- {name}{result['signature']}")
                else:
                    print(f"- {name}: {result.get('error')}")

    if failed:
        print("\nMissing or broken dependencies: " + ", ".join(failed), file=sys.stderr)
        print("Install compatible dgllife, DGL, PyTorch, RDKit, and scientific Python dependencies before running workflow-specific code.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
