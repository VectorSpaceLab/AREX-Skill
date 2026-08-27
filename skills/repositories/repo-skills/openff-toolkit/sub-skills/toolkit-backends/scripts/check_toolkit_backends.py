#!/usr/bin/env python3
"""Inspect OpenFF Toolkit backend wrapper availability safely.

The helper avoids requiring optional backend dependencies. It exits with status 0
unless --require names one or more wrappers that are unavailable.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


WRAPPER_NAMES = {
    "rdkit": "RDKitToolkitWrapper",
    "openeye": "OpenEyeToolkitWrapper",
    "ambertools": "AmberToolsToolkitWrapper",
    "nagl": "NAGLToolkitWrapper",
    "builtin": "BuiltInToolkitWrapper",
    "built-in": "BuiltInToolkitWrapper",
    "built_in": "BuiltInToolkitWrapper",
}


def _stringify(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _stringify(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_stringify(item) for item in value]
    if isinstance(value, type):
        return value.__name__
    return str(value)


def _load_openff() -> tuple[dict[str, Any], dict[str, type], Any | None]:
    try:
        from openff.toolkit import __version__ as toolkit_version
        from openff.toolkit.utils.toolkits import GLOBAL_TOOLKIT_REGISTRY
        from openff.toolkit.utils.toolkits import AmberToolsToolkitWrapper
        from openff.toolkit.utils.toolkits import BuiltInToolkitWrapper
        from openff.toolkit.utils.toolkits import NAGLToolkitWrapper
        from openff.toolkit.utils.toolkits import OpenEyeToolkitWrapper
        from openff.toolkit.utils.toolkits import RDKitToolkitWrapper
    except Exception as exc:  # pragma: no cover - diagnostic path
        return (
            {
                "openff_toolkit_importable": False,
                "import_error": {"type": type(exc).__name__, "message": str(exc)},
            },
            {},
            None,
        )

    wrappers = {
        "rdkit": RDKitToolkitWrapper,
        "openeye": OpenEyeToolkitWrapper,
        "ambertools": AmberToolsToolkitWrapper,
        "nagl": NAGLToolkitWrapper,
        "builtin": BuiltInToolkitWrapper,
    }
    metadata = {
        "openff_toolkit_importable": True,
        "openff_toolkit_version": toolkit_version,
    }
    return metadata, wrappers, GLOBAL_TOOLKIT_REGISTRY


def _availability(wrapper_key: str, wrapper_class: type) -> dict[str, Any]:
    result: dict[str, Any] = {
        "key": wrapper_key,
        "class": wrapper_class.__name__,
        "available": False,
        "is_available_result": None,
        "instantiable": False,
        "toolkit_name": getattr(wrapper_class, "_toolkit_name", None),
        "toolkit_version": None,
        "toolkit_installation_instructions": getattr(
            wrapper_class,
            "_toolkit_installation_instructions",
            None,
        ),
        "supported_charge_methods": [],
        "toolkit_file_read_formats": [],
        "toolkit_file_write_formats": [],
        "error": None,
    }

    if wrapper_key == "builtin":
        result["available"] = True
        result["is_available_result"] = True
    else:
        try:
            is_available = wrapper_class.is_available()
        except Exception as exc:
            result["is_available_result"] = {
                "type": type(exc).__name__,
                "message": str(exc),
            }
        else:
            result["is_available_result"] = _stringify(is_available)
            result["available"] = bool(is_available)

    try:
        wrapper = wrapper_class()
    except Exception as exc:
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
        return result

    result["instantiable"] = True
    result["available"] = True
    result["toolkit_name"] = wrapper.toolkit_name
    result["toolkit_version"] = _stringify(wrapper.toolkit_version)
    result["toolkit_installation_instructions"] = wrapper.toolkit_installation_instructions
    result["supported_charge_methods"] = sorted(_stringify(wrapper.supported_charge_methods))
    result["toolkit_file_read_formats"] = sorted(_stringify(wrapper.toolkit_file_read_formats))
    result["toolkit_file_write_formats"] = sorted(_stringify(wrapper.toolkit_file_write_formats))
    return result


def _registry_summary(global_registry: Any | None) -> dict[str, Any]:
    if global_registry is None:
        return {"registered_toolkits": [], "registered_toolkit_versions": {}}
    registered = global_registry.registered_toolkits
    return {
        "registered_toolkits": [
            {
                "class": type(wrapper).__name__,
                "toolkit_name": wrapper.toolkit_name,
                "toolkit_version": _stringify(wrapper.toolkit_version),
            }
            for wrapper in registered
        ],
        "registered_toolkit_versions": _stringify(global_registry.registered_toolkit_versions),
    }


def inspect_backends() -> dict[str, Any]:
    metadata, wrappers, global_registry = _load_openff()
    report: dict[str, Any] = dict(metadata)
    report["wrappers"] = {
        wrapper_key: _availability(wrapper_key, wrapper_class)
        for wrapper_key, wrapper_class in wrappers.items()
    }
    report["global_registry"] = _registry_summary(global_registry)
    report["aliases"] = WRAPPER_NAMES
    return report


def _normalize_required(names: list[str]) -> tuple[list[str], list[str]]:
    normalized: list[str] = []
    unknown: list[str] = []
    for name in names:
        key = name.strip().lower().replace("-", "_")
        if key == "built_in":
            key = "builtin"
        elif key == "open_eye":
            key = "openeye"
        elif key == "amber_tools":
            key = "ambertools"
        if key in {"rdkit", "openeye", "ambertools", "nagl", "builtin"}:
            normalized.append(key)
        else:
            unknown.append(name)
    return normalized, unknown


def _print_text(report: dict[str, Any]) -> None:
    if not report.get("openff_toolkit_importable"):
        error = report.get("import_error", {})
        print(f"OpenFF Toolkit import failed: {error.get('type')}: {error.get('message')}")
        return

    print(f"OpenFF Toolkit version: {report.get('openff_toolkit_version')}")
    print("Global registry:")
    for wrapper in report["global_registry"]["registered_toolkits"]:
        print(f"  - {wrapper['class']}: {wrapper['toolkit_name']} {wrapper['toolkit_version']}")
    if not report["global_registry"]["registered_toolkits"]:
        print("  - <empty>")

    print("Wrappers:")
    for key, info in report["wrappers"].items():
        status = "available" if info["available"] else "unavailable"
        instantiable = "instantiable" if info["instantiable"] else "not instantiable"
        print(f"  - {key}: {info['class']} ({status}, {instantiable})")
        if info["supported_charge_methods"]:
            print(f"    charges: {', '.join(info['supported_charge_methods'])}")
        if info["toolkit_file_read_formats"]:
            print(f"    reads: {', '.join(info['toolkit_file_read_formats'])}")
        if info["toolkit_file_write_formats"]:
            print(f"    writes: {', '.join(info['toolkit_file_write_formats'])}")
        if info["error"]:
            print(f"    error: {info['error']['type']}: {info['error']['message']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect OpenFF Toolkit backend wrappers and global ToolkitRegistry.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--require",
        nargs="+",
        default=[],
        metavar="NAME",
        help="Require wrappers by key: rdkit, openeye, ambertools, nagl, builtin.",
    )
    args = parser.parse_args(argv)

    report = inspect_backends()
    required, unknown = _normalize_required(args.require)
    missing = [
        key
        for key in required
        if not report.get("wrappers", {}).get(key, {}).get("available", False)
    ]
    report["requirements"] = {
        "requested": args.require,
        "normalized": required,
        "unknown": unknown,
        "missing": missing,
        "ok": not unknown and not missing,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
        if unknown:
            print(f"Unknown required wrapper names: {', '.join(unknown)}", file=sys.stderr)
        if missing:
            print(f"Missing required wrappers: {', '.join(missing)}", file=sys.stderr)

    if unknown or missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
