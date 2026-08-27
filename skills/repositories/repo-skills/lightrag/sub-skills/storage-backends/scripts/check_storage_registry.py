#!/usr/bin/env python3
"""Read-only LightRAG storage registry check.

This script intentionally avoids instantiating storage classes or importing
optional backend implementation modules. It only imports the public registry
from ``lightrag.kg`` and package metadata for console-script discovery.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import sys
from typing import Any

EXPECTED_CATEGORIES = {
    "KV_STORAGE": {
        "JsonKVStorage",
        "RedisKVStorage",
        "PGKVStorage",
        "MongoKVStorage",
        "OpenSearchKVStorage",
    },
    "VECTOR_STORAGE": {
        "NanoVectorDBStorage",
        "MilvusVectorDBStorage",
        "PGVectorStorage",
        "FaissVectorDBStorage",
        "QdrantVectorDBStorage",
        "MongoVectorDBStorage",
        "OpenSearchVectorDBStorage",
    },
    "GRAPH_STORAGE": {
        "NetworkXStorage",
        "Neo4JStorage",
        "PGGraphStorage",
        "MongoGraphStorage",
        "MemgraphStorage",
        "OpenSearchGraphStorage",
    },
    "DOC_STATUS_STORAGE": {
        "JsonDocStatusStorage",
        "RedisDocStatusStorage",
        "PGDocStatusStorage",
        "MongoDocStatusStorage",
        "OpenSearchDocStatusStorage",
    },
}

EXPECTED_CONSOLE_SCRIPTS = {
    "lightrag-rebuild-vdb",
    "lightrag-clean-llmqc",
    "lightrag-download-cache",
}


def _console_scripts() -> dict[str, str]:
    scripts: dict[str, str] = {}
    for entry_point in metadata.entry_points().select(group="console_scripts"):
        if entry_point.name.startswith("lightrag-"):
            scripts[entry_point.name] = entry_point.value
    return scripts


def _as_sorted_dict(mapping: dict[str, set[str]]) -> dict[str, list[str]]:
    return {key: sorted(value) for key, value in sorted(mapping.items())}


def collect() -> dict[str, Any]:
    from lightrag.kg import (  # Imported here so --help works without LightRAG.
        STORAGE_ENV_REQUIREMENTS,
        STORAGE_IMPLEMENTATIONS,
        STORAGES,
        verify_storage_implementation,
    )

    categories: dict[str, set[str]] = {}
    verification_errors: list[str] = []

    for category, info in sorted(STORAGE_IMPLEMENTATIONS.items()):
        implementations = set(info.get("implementations", []))
        categories[category] = implementations
        for storage_name in sorted(implementations):
            try:
                verify_storage_implementation(category, storage_name)
            except Exception as exc:  # pragma: no cover - defensive report path
                verification_errors.append(f"{category}:{storage_name}: {exc}")

    expected_missing = {
        category: expected - categories.get(category, set())
        for category, expected in EXPECTED_CATEGORIES.items()
    }
    unexpected = {
        category: categories.get(category, set()) - EXPECTED_CATEGORIES.get(category, set())
        for category in categories
    }

    registry_names = set().union(*categories.values()) if categories else set()
    module_mapping_names = set(STORAGES)
    env_names = set(STORAGE_ENV_REQUIREMENTS)
    scripts = _console_scripts()

    warnings: list[str] = []
    for alias in sorted(module_mapping_names - registry_names):
        warnings.append(
            f"{alias} is import-mapped but not listed as a compatible storage implementation"
        )
    for name in sorted(registry_names - module_mapping_names):
        warnings.append(f"{name} is registered but missing from STORAGES module mapping")
    for name in sorted(registry_names - env_names):
        warnings.append(f"{name} has no STORAGE_ENV_REQUIREMENTS entry")

    missing_console_scripts = EXPECTED_CONSOLE_SCRIPTS - set(scripts)

    ok = (
        not any(expected_missing.values())
        and not verification_errors
        and not missing_console_scripts
    )

    return {
        "ok": ok,
        "categories": _as_sorted_dict(categories),
        "required_env": {
            name: list(values)
            for name, values in sorted(STORAGE_ENV_REQUIREMENTS.items())
            if name in registry_names
        },
        "module_mapping_only": sorted(module_mapping_names - registry_names),
        "unexpected_registered": _as_sorted_dict(
            {key: value for key, value in unexpected.items() if value}
        ),
        "expected_missing": _as_sorted_dict(
            {key: value for key, value in expected_missing.items() if value}
        ),
        "verification_errors": verification_errors,
        "console_scripts": {name: scripts.get(name) for name in sorted(EXPECTED_CONSOLE_SCRIPTS & set(scripts))},
        "missing_console_scripts": sorted(missing_console_scripts),
        "warnings": warnings,
    }


def print_human(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "FAILED"
    print(f"LightRAG storage registry check: {status}")
    print()

    for category, names in report["categories"].items():
        print(f"{category}:")
        for name in names:
            env_vars = report["required_env"].get(name, [])
            env_text = ", ".join(env_vars) if env_vars else "no required env vars"
            print(f"  - {name} ({env_text})")
        print()

    if report["module_mapping_only"]:
        print("Import-mapped but not category-compatible:")
        for name in report["module_mapping_only"]:
            print(f"  - {name}")
        print()

    if report["console_scripts"]:
        print("Console scripts:")
        for name, target in report["console_scripts"].items():
            print(f"  - {name}: {target}")
        print()

    for field in ("expected_missing", "unexpected_registered", "verification_errors", "missing_console_scripts"):
        value = report[field]
        if value:
            print(f"{field}:")
            if isinstance(value, dict):
                for key, items in value.items():
                    print(f"  - {key}: {', '.join(items)}")
            else:
                for item in value:
                    print(f"  - {item}")
            print()

    if report["warnings"]:
        print("Warnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args(argv)

    try:
        report = collect()
    except Exception as exc:
        error_report = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(error_report, indent=2, sort_keys=True))
        else:
            print(f"LightRAG storage registry check: FAILED\n{error_report['error']}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
