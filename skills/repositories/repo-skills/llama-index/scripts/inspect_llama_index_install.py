#!/usr/bin/env python3
"""Inspect installed LlamaIndex distributions and import roots without network calls."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class DistributionStatus:
    name: str
    installed: bool
    version: str | None = None
    summary: str | None = None
    error: str | None = None


@dataclass
class ImportStatus:
    module: str
    importable: bool
    version: str | None = None
    error: str | None = None


def inspect_distribution(name: str) -> DistributionStatus:
    try:
        dist = metadata.distribution(name)
    except metadata.PackageNotFoundError as exc:
        return DistributionStatus(name=name, installed=False, error=str(exc))
    return DistributionStatus(
        name=name,
        installed=True,
        version=dist.version,
        summary=dist.metadata.get("Summary"),
    )


def inspect_import(module: str) -> ImportStatus:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return ImportStatus(module=module, importable=False, error=f"{type(exc).__name__}: {exc}")
    return ImportStatus(
        module=module,
        importable=True,
        version=getattr(imported, "__version__", None),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dist",
        action="append",
        default=[],
        help="Distribution to inspect. Can be repeated. Defaults to common LlamaIndex packages.",
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="Import module to inspect. Can be repeated. Defaults to llama_index.core.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    distributions = args.dist or [
        "llama-index",
        "llama-index-core",
        "llama-index-workflows",
        "llama-index-llms-openai",
        "llama-index-embeddings-openai",
    ]
    modules = args.module or ["llama_index.core"]

    result: dict[str, Any] = {
        "distributions": [asdict(inspect_distribution(name)) for name in distributions],
        "imports": [asdict(inspect_import(module)) for module in modules],
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for item in result["distributions"]:
            marker = "ok" if item["installed"] else "missing"
            version = f" {item['version']}" if item.get("version") else ""
            print(f"dist {item['name']}: {marker}{version}")
        for item in result["imports"]:
            marker = "ok" if item["importable"] else "missing"
            version = f" {item['version']}" if item.get("version") else ""
            print(f"import {item['module']}: {marker}{version}")

    failed = any(not item["installed"] for item in result["distributions"] if item["name"] == "llama-index-core")
    failed = failed or any(not item["importable"] for item in result["imports"] if item["module"] == "llama_index.core")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
