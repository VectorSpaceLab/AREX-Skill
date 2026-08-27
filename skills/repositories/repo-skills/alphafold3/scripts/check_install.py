#!/usr/bin/env python3
"""Safe AlphaFold 3 installation/resource check.

This script imports lightweight AlphaFold 3 modules, reports version and JSON
facts, and checks for generated CCD resource files when package locations are
available. It does not run the data pipeline or model inference.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.resources
import inspect
import sys


def _print_result(label: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"{status}: {label}{suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    try:
        version = importlib.metadata.version("alphafold3")
        _print_result("distribution alphafold3", True, version)
    except Exception as exc:  # pragma: no cover - diagnostic script
        _print_result("distribution alphafold3", False, str(exc))
        return 2

    modules = [
        "alphafold3",
        "alphafold3.common.folding_input",
        "alphafold3.data.pipeline",
        "alphafold3.model.model_config",
        "alphafold3.structure",
    ]
    imported = {}
    failed = False
    for module_name in modules:
        try:
            imported[module_name] = importlib.import_module(module_name)
            _print_result(f"import {module_name}", True)
        except Exception as exc:  # pragma: no cover - diagnostic script
            failed = True
            _print_result(f"import {module_name}", False, f"{type(exc).__name__}: {exc}")

    folding_input = imported.get("alphafold3.common.folding_input")
    if folding_input is not None:
        _print_result("JSON dialect", True, getattr(folding_input, "JSON_DIALECT", "unknown"))
        _print_result("JSON version", True, str(getattr(folding_input, "JSON_VERSION", "unknown")))
        print("Input.from_json signature:", inspect.signature(folding_input.Input.from_json))

    try:
        converter_root = importlib.resources.files("alphafold3.constants.converters")
        for resource_name in ("ccd.pickle", "chemical_component_sets.pickle"):
            resource = converter_root.joinpath(resource_name)
            _print_result(f"resource {resource_name}", resource.is_file())
    except Exception as exc:  # pragma: no cover - diagnostic script
        failed = True
        _print_result("generated CCD resource inspection", False, f"{type(exc).__name__}: {exc}")

    if failed:
        print("One or more checks failed. See references/troubleshooting.md in the alphafold3 skill.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
