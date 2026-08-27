#!/usr/bin/env python3
"""No-secret PyRIT setup/memory/registry introspection smoke."""
from __future__ import annotations

import argparse
import importlib
import inspect
import json

OBJECTS = [
    ("pyrit.setup", "initialize_pyrit_async"),
    ("pyrit.setup", "initialize_from_config_async"),
    ("pyrit.memory", "CentralMemory"),
    ("pyrit.memory", "SQLiteMemory"),
    ("pyrit.registry.components.converter_registry", "ConverterRegistry"),
    ("pyrit.output.helpers", "output_score_async"),
    ("pyrit.models", "Score"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect setup, memory, registry, output, and model APIs without side effects.")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args()
    checks = []
    ok = True
    errors = []
    for module_name, attr in OBJECTS:
        try:
            obj = getattr(importlib.import_module(module_name), attr)
            checks.append({"object": f"{module_name}.{attr}", "signature": str(inspect.signature(obj))[:500]})
        except Exception as exc:  # noqa: BLE001
            ok = False
            errors.append(f"{module_name}.{attr}: {type(exc).__name__}: {exc}")
    result = {"ok": ok, "checks": checks, "errors": errors}
    print(json.dumps(result, indent=2) if args.json else result)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
