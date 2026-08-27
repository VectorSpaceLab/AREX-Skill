#!/usr/bin/env python3
"""List REINVENT4 scoring components discovered from installed plugins.

The script inspects the installed ``reinvent_plugins.components`` namespace and
prints component classes found in ``comp_*`` modules. It does not run scoring,
instantiate components, load model checkpoints, or call external services.
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib
import json
import pathlib
import pkgutil
import sys
from typing import Any


TAG_COMPONENT = "__component"
TAG_PARAMETERS = "__parameters"


def clean_name(name: str) -> str:
    return name.lower().replace("-", "").replace("_", "")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect installed reinvent_plugins.components comp_* modules and tagged classes."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text table.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include imported modules with no tagged components and import-error details.",
    )
    parser.add_argument(
        "--fail-on-import-error",
        action="store_true",
        help="Exit non-zero if any comp_* module cannot be imported.",
    )
    return parser.parse_args()


def iter_component_modules() -> tuple[list[str], list[dict[str, str]]]:
    cwd = str(pathlib.Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    try:
        from reinvent_plugins import components
    except Exception as exc:  # pragma: no cover - depends on target env
        return [], [{"module": "reinvent_plugins.components", "error": repr(exc)}]

    module_names: list[str] = []
    errors: list[dict[str, str]] = []

    if not hasattr(components, "__path__"):
        errors.append(
            {
                "module": "reinvent_plugins.components",
                "error": "not a package or namespace package with __path__",
            }
        )
        return module_names, errors

    for module_info in pkgutil.walk_packages(components.__path__, components.__name__ + "."):
        if module_info.ispkg:
            continue
        basename = module_info.name.rsplit(".", 1)[-1]
        if basename.startswith("comp_"):
            module_names.append(module_info.name)

    return sorted(module_names), errors


def inspect_module(module_name: str) -> dict[str, Any]:
    record: dict[str, Any] = {"module": module_name, "components": [], "parameter_class": None}
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # keep scanning other plugins
        record["error"] = repr(exc)
        return record

    parameter_class = None
    components: list[dict[str, Any]] = []

    for attr_name, attr in vars(module).items():
        if not isinstance(attr, type):
            continue
        if TAG_PARAMETERS in vars(attr) and dataclasses.is_dataclass(attr):
            parameter_class = attr.__name__
        if TAG_COMPONENT in vars(attr):
            role = getattr(attr, TAG_COMPONENT)
            if role is True:
                role = "scorer"
            elif role == "True":
                role = "scorer"
            components.append(
                {
                    "class": attr.__name__,
                    "lookup_key": clean_name(attr.__name__),
                    "role": str(role),
                }
            )

    record["components"] = sorted(components, key=lambda item: item["lookup_key"])
    record["parameter_class"] = parameter_class
    return record


def main() -> int:
    args = parse_args()
    module_names, initial_errors = iter_component_modules()
    records = [inspect_module(name) for name in module_names]

    import_errors = initial_errors + [
        {"module": record["module"], "error": record["error"]}
        for record in records
        if "error" in record
    ]

    payload = {
        "module_count": len(module_names),
        "component_count": sum(len(record.get("components", [])) for record in records),
        "modules": records if args.verbose else [r for r in records if r.get("components")],
        "import_errors": import_errors,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Scanned comp_* modules: {payload['module_count']}")
        print(f"Discovered component classes: {payload['component_count']}")
        if import_errors:
            print("\nImport errors:")
            for error in import_errors:
                print(f"  - {error['module']}: {error['error']}")
        print("\nComponents:")
        for record in payload["modules"]:
            if "error" in record:
                if args.verbose:
                    print(f"  - {record['module']}: import failed")
                continue
            if not record.get("components"):
                if args.verbose:
                    print(f"  - {record['module']}: no tagged components")
                continue
            param = record.get("parameter_class") or "none"
            print(f"  - {record['module']} (parameters: {param})")
            for component in record["components"]:
                print(
                    "      "
                    f"{component['class']} "
                    f"lookup={component['lookup_key']} "
                    f"role={component['role']}"
                )

    if import_errors and args.fail_on_import_error:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
