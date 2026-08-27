#!/usr/bin/env python3
"""Check SchNetPack imports and important public signatures."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
import sys
from typing import Any


TARGETS = [
    ("schnetpack.data", "ASEAtomsData"),
    ("schnetpack.data", "AtomsDataModule"),
    ("schnetpack.data", "create_dataset"),
    ("schnetpack.data", "load_dataset"),
    ("schnetpack.model", "NeuralNetworkPotential"),
    ("schnetpack.representation", "SchNet"),
    ("schnetpack.representation", "PaiNN"),
    ("schnetpack.atomistic", "Atomwise"),
    ("schnetpack.atomistic", "Forces"),
    ("schnetpack.interfaces", "SpkCalculator"),
    ("schnetpack.interfaces", "AtomsConverter"),
]


def collect() -> dict[str, Any]:
    result: dict[str, Any] = {"ok": False, "imports": {}, "signatures": {}, "errors": []}
    try:
        spk = importlib.import_module("schnetpack")
        result["version"] = getattr(spk, "__version__", None)
        result["distribution_version"] = metadata.version("schnetpack")
        result["imports"]["schnetpack"] = True
    except Exception as exc:  # pragma: no cover - diagnostic script
        result["errors"].append(f"import schnetpack failed: {exc}")
        return result

    for module_name in [
        "schnetpack.data",
        "schnetpack.representation",
        "schnetpack.atomistic",
        "schnetpack.interfaces",
        "schnetpack.md",
    ]:
        try:
            importlib.import_module(module_name)
            result["imports"][module_name] = True
        except Exception as exc:  # pragma: no cover - diagnostic script
            result["imports"][module_name] = False
            result["errors"].append(f"import {module_name} failed: {exc}")

    for module_name, object_name in TARGETS:
        try:
            module = importlib.import_module(module_name)
            obj = getattr(module, object_name)
            result["signatures"][f"{module_name}.{object_name}"] = str(inspect.signature(obj))
        except Exception as exc:  # pragma: no cover - diagnostic script
            result["errors"].append(f"signature {module_name}.{object_name} failed: {exc}")

    result["ok"] = not result["errors"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    args = parser.parse_args()

    result = collect()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"ok: {result['ok']}")
        if "version" in result:
            print(f"schnetpack: {result['version']}")
        for key, value in result["imports"].items():
            print(f"import {key}: {value}")
        for key, value in result["signatures"].items():
            print(f"{key}{value}")
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
