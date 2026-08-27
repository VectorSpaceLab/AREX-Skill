#!/usr/bin/env python3
"""Read-only Mem0 Python SDK inspection helper.

This script imports the installed `mem0` package and reports public exports,
version, module origin, and method signatures. It does not instantiate hosted
clients or local Memory objects, so it does not require API keys or providers.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from typing import Any

EXPORTS = ("Memory", "AsyncMemory", "MemoryClient", "AsyncMemoryClient")
METHODS = (
    "__init__",
    "add",
    "search",
    "get",
    "get_all",
    "update",
    "delete",
    "delete_all",
    "history",
    "reset",
    "batch_update",
    "batch_delete",
    "create_memory_export",
    "get_memory_export",
    "feedback",
)


def _signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<signature unavailable>"


def inspect_sdk(include_private_path: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {
        "ok": False,
        "package": "mem0ai",
        "import_name": "mem0",
        "version": None,
        "module_file": None,
        "exports": {},
        "errors": [],
    }

    try:
        mem0 = importlib.import_module("mem0")
    except Exception as exc:  # pragma: no cover - depends on user environment
        report["errors"].append(f"Failed to import mem0: {exc}")
        return report

    report["ok"] = True
    report["version"] = getattr(mem0, "__version__", None)
    if include_private_path:
        report["module_file"] = getattr(mem0, "__file__", None)

    for export_name in EXPORTS:
        exported = getattr(mem0, export_name, None)
        if exported is None:
            report["exports"][export_name] = {"available": False}
            continue

        methods: dict[str, str] = {}
        for method_name in METHODS:
            method = getattr(exported, method_name, None)
            if method is not None:
                methods[method_name] = _signature(method)

        report["exports"][export_name] = {
            "available": True,
            "module": getattr(exported, "__module__", None),
            "signature": _signature(exported),
            "methods": methods,
        }

    return report


def print_text(report: dict[str, Any]) -> None:
    if not report["ok"]:
        print("Mem0 Python SDK import failed.")
        for error in report["errors"]:
            print(f"- {error}")
        return

    print(f"Mem0 Python SDK import: ok")
    print(f"Distribution: {report['package']}")
    print(f"Version: {report.get('version') or '<unknown>'}")
    if report.get("module_file"):
        print(f"Module file: {report['module_file']}")
    print("Public exports:")

    for export_name, export_info in report["exports"].items():
        if not export_info.get("available"):
            print(f"- {export_name}: missing")
            continue
        print(f"- {export_name}: {export_info.get('signature')}")
        for method_name, signature in export_info.get("methods", {}).items():
            if method_name == "__init__":
                print(f"  - constructor {signature}")
            else:
                print(f"  - {method_name}{signature}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect installed Mem0 Python SDK exports and method signatures without credentials."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--include-private-path",
        action="store_true",
        help="Include mem0.__file__ in output. Avoid this in public reports because it may reveal local paths.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = inspect_sdk(include_private_path=args.include_private_path)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
