#!/usr/bin/env python3
"""Check OpenFF Toolkit import, version, force-field discovery, and backend wrappers.

Example:
    python check_openff_toolkit.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib import metadata


def wrapper_info(wrapper_class):
    item = {
        "class": wrapper_class.__name__,
        "available": False,
        "instantiable": False,
        "toolkit_name": None,
        "toolkit_version": None,
        "supported_charge_methods": [],
        "read_formats": [],
        "write_formats": [],
        "error": None,
    }
    try:
        item["available"] = bool(wrapper_class.is_available())
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report all failures.
        item["error"] = {"type": type(exc).__name__, "message": str(exc)}
    try:
        wrapper = wrapper_class()
        item["instantiable"] = True
        for key, attr in [
            ("toolkit_name", "toolkit_name"),
            ("toolkit_version", "toolkit_version"),
            ("supported_charge_methods", "supported_charge_methods"),
            ("read_formats", "toolkit_file_read_formats"),
            ("write_formats", "toolkit_file_write_formats"),
        ]:
            try:
                value = getattr(wrapper, attr)
                item[key] = value() if callable(value) else value
            except Exception as exc:  # noqa: BLE001
                item.setdefault("attribute_errors", {})[attr] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:  # noqa: BLE001
        item["error"] = {"type": type(exc).__name__, "message": str(exc)}
    return item


def collect():
    report = {
        "openff_toolkit_importable": False,
        "distribution_version": None,
        "module_version": None,
        "core_classes": {},
        "available_force_fields": [],
        "global_registry": {},
        "wrappers": {},
        "errors": [],
    }
    try:
        report["distribution_version"] = metadata.version("openff-toolkit")
    except Exception as exc:  # noqa: BLE001
        report["errors"].append({"phase": "metadata", "type": type(exc).__name__, "message": str(exc)})
    try:
        import openff.toolkit as toolkit
        from openff.toolkit import ForceField, Molecule, Topology
        from openff.toolkit.typing.engines.smirnoff import get_available_force_fields
        from openff.toolkit.utils.toolkits import (
            GLOBAL_TOOLKIT_REGISTRY,
            AmberToolsToolkitWrapper,
            BuiltInToolkitWrapper,
            NAGLToolkitWrapper,
            OpenEyeToolkitWrapper,
            RDKitToolkitWrapper,
        )

        report["openff_toolkit_importable"] = True
        report["module_version"] = getattr(toolkit, "__version__", None)
        report["core_classes"] = {
            "Molecule": Molecule.__module__ + "." + Molecule.__name__,
            "Topology": Topology.__module__ + "." + Topology.__name__,
            "ForceField": ForceField.__module__ + "." + ForceField.__name__,
        }
        try:
            report["available_force_fields"] = list(get_available_force_fields())
        except Exception as exc:  # noqa: BLE001
            report["errors"].append({"phase": "force-field-discovery", "type": type(exc).__name__, "message": str(exc)})
        try:
            report["global_registry"] = {
                "registered_toolkit_versions": dict(GLOBAL_TOOLKIT_REGISTRY.registered_toolkit_versions),
                "registered_toolkits": [type(wrapper).__name__ for wrapper in GLOBAL_TOOLKIT_REGISTRY.registered_toolkits],
            }
        except Exception as exc:  # noqa: BLE001
            report["errors"].append({"phase": "global-registry", "type": type(exc).__name__, "message": str(exc)})
        for key, cls in {
            "rdkit": RDKitToolkitWrapper,
            "openeye": OpenEyeToolkitWrapper,
            "ambertools": AmberToolsToolkitWrapper,
            "nagl": NAGLToolkitWrapper,
            "builtin": BuiltInToolkitWrapper,
        }.items():
            report["wrappers"][key] = wrapper_info(cls)
    except Exception as exc:  # noqa: BLE001
        report["errors"].append({"phase": "import", "type": type(exc).__name__, "message": str(exc)})
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check OpenFF Toolkit runtime availability.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--require-force-field",
        default=None,
        help="Fail if the named installed force field is not discoverable, e.g. openff-2.3.0.offxml.",
    )
    parser.add_argument(
        "--require-wrapper",
        action="append",
        default=[],
        choices=["rdkit", "openeye", "ambertools", "nagl", "builtin"],
        help="Fail if the named wrapper is unavailable. May be repeated.",
    )
    args = parser.parse_args(argv)
    report = collect()
    ok = bool(report["openff_toolkit_importable"])
    if args.require_force_field and args.require_force_field not in report.get("available_force_fields", []):
        ok = False
        report["errors"].append(
            {
                "phase": "require-force-field",
                "type": "MissingForceField",
                "message": f"Required force field not discoverable: {args.require_force_field}",
            }
        )
    for key in args.require_wrapper:
        if not report.get("wrappers", {}).get(key, {}).get("available"):
            ok = False
            report["errors"].append(
                {"phase": "require-wrapper", "type": "MissingWrapper", "message": f"Required wrapper unavailable: {key}"}
            )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"OpenFF Toolkit importable: {report['openff_toolkit_importable']}")
        print(f"Distribution version: {report['distribution_version']}")
        print(f"Module version: {report['module_version']}")
        print("Wrappers:")
        for key, item in report.get("wrappers", {}).items():
            print(f"  {key}: available={item.get('available')} name={item.get('toolkit_name')} version={item.get('toolkit_version')}")
        if report["errors"]:
            print("Errors:")
            for error in report["errors"]:
                print(f"  {error['phase']}: {error['type']}: {error['message']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
