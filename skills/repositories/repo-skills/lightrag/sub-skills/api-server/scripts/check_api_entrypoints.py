#!/usr/bin/env python3
"""Read-only LightRAG API entrypoint check.

The check imports API modules and inspects installed console scripts without
starting Uvicorn, Gunicorn, storage backends, model calls, or external services.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import sys
from typing import Any

EXPECTED_CONSOLE_SCRIPTS = {
    "lightrag-server": "lightrag.api.lightrag_server:main",
    "lightrag-gunicorn": "lightrag.api.run_with_gunicorn:main",
    "lightrag-hash-password": "lightrag.tools.hash_password:main",
}

EXPECTED_MODULES = [
    "lightrag.api.config",
    "lightrag.api.auth",
    "lightrag.api.passwords",
    "lightrag.api.lightrag_server",
    "lightrag.api.routers.document_routes",
    "lightrag.api.routers.query_routes",
    "lightrag.api.routers.graph_routes",
    "lightrag.api.routers.ollama_api",
    "lightrag.tools.hash_password",
]

EXPECTED_ROUTE_FACTORIES = {
    "lightrag.api.routers.document_routes": "create_document_routes",
    "lightrag.api.routers.query_routes": "create_query_routes",
    "lightrag.api.routers.graph_routes": "create_graph_routes",
    "lightrag.api.routers.ollama_api": "OllamaAPI",
}


def _console_scripts() -> dict[str, str]:
    scripts: dict[str, str] = {}
    for entry_point in metadata.entry_points().select(group="console_scripts"):
        if entry_point.name.startswith("lightrag-"):
            scripts[entry_point.name] = entry_point.value
    return scripts


def _set_safe_import_defaults() -> dict[str, str | None]:
    """Set minimal defaults that avoid importing local .env/provider surprises."""
    defaults = {
        "LLM_BINDING": "ollama",
        "EMBEDDING_BINDING": "ollama",
        "AUTH_ACCOUNTS": "",
        "TOKEN_SECRET": "",
        "LIGHTRAG_API_KEY": "",
    }
    previous: dict[str, str | None] = {}
    for key, value in defaults.items():
        previous[key] = os.environ.get(key)
        os.environ[key] = value
    return previous


def _restore_env(previous: dict[str, str | None]) -> None:
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _import_modules() -> tuple[dict[str, bool], list[str]]:
    imported: dict[str, bool] = {}
    errors: list[str] = []
    previous_argv = sys.argv[:]
    previous_env = _set_safe_import_defaults()
    try:
        sys.argv = ["check_api_entrypoints.py"]
        for module_name in EXPECTED_MODULES:
            try:
                importlib.import_module(module_name)
                imported[module_name] = True
            except Exception as exc:  # pragma: no cover - defensive report path
                imported[module_name] = False
                errors.append(f"{module_name}: {type(exc).__name__}: {exc}")
    finally:
        sys.argv = previous_argv
        _restore_env(previous_env)
    return imported, errors


def _route_factory_report() -> dict[str, bool]:
    report: dict[str, bool] = {}
    for module_name, attr_name in EXPECTED_ROUTE_FACTORIES.items():
        module = sys.modules.get(module_name)
        report[f"{module_name}:{attr_name}"] = bool(
            module is not None and hasattr(module, attr_name)
        )
    return report


def collect() -> dict[str, Any]:
    scripts = _console_scripts()
    imported, import_errors = _import_modules()
    route_factories = _route_factory_report()

    missing_scripts = {
        name: target
        for name, target in EXPECTED_CONSOLE_SCRIPTS.items()
        if scripts.get(name) != target
    }
    present_scripts = {
        name: scripts.get(name)
        for name in sorted(EXPECTED_CONSOLE_SCRIPTS)
        if scripts.get(name) == EXPECTED_CONSOLE_SCRIPTS[name]
    }
    missing_route_factories = [
        name for name, present in sorted(route_factories.items()) if not present
    ]

    try:
        version = metadata.version("lightrag-hku")
    except metadata.PackageNotFoundError:
        version = None

    ok = not missing_scripts and not import_errors and not missing_route_factories

    return {
        "ok": ok,
        "package_version": version,
        "console_scripts": present_scripts,
        "missing_or_mismatched_console_scripts": missing_scripts,
        "imported_modules": imported,
        "import_errors": import_errors,
        "route_factories": route_factories,
        "missing_route_factories": missing_route_factories,
        "notes": [
            "This check does not start the API server.",
            "Guest-mode JWT warnings during import are expected when auth is disabled.",
        ],
    }


def print_human(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAILED"
    print(f"LightRAG API entrypoint check: {status}")
    print()

    if report["package_version"]:
        print(f"Package version: {report['package_version']}")
    else:
        print("Package version: not found via installed metadata")
    print()

    print("Console scripts:")
    if report["console_scripts"]:
        for name, target in report["console_scripts"].items():
            print(f"  - {name}: {target}")
    else:
        print("  - none of the expected API scripts were found")
    print()

    print("Imported modules:")
    for module_name, imported in report["imported_modules"].items():
        marker = "ok" if imported else "failed"
        print(f"  - {module_name}: {marker}")
    print()

    print("Route factories:")
    for name, present in report["route_factories"].items():
        marker = "ok" if present else "missing"
        print(f"  - {name}: {marker}")
    print()

    if report["missing_or_mismatched_console_scripts"]:
        print("Missing or mismatched console scripts:")
        for name, expected in report["missing_or_mismatched_console_scripts"].items():
            print(f"  - {name}: expected {expected}")
        print()

    if report["import_errors"]:
        print("Import errors:")
        for error in report["import_errors"]:
            print(f"  - {error}")
        print()

    if report["missing_route_factories"]:
        print("Missing route factories:")
        for name in report["missing_route_factories"]:
            print(f"  - {name}")
        print()

    print("Notes:")
    for note in report["notes"]:
        print(f"  - {note}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args(argv)

    try:
        report = collect()
    except Exception as exc:  # pragma: no cover - defensive report path
        report = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"LightRAG API entrypoint check: FAILED\n{report['error']}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
