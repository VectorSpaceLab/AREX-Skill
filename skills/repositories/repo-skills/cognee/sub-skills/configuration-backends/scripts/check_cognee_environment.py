#!/usr/bin/env python3
"""Inspect a Cognee installation and summarize config/back-end readiness.

Safe by default:
- no network calls
- no data mutation
- no service startup
- no secret printing

It reports whether key config classes import, whether the installed Cognee
package is present, and whether optional modules for selected providers are
available.
"""

from __future__ import annotations

import argparse
import json
import importlib.util
from dataclasses import asdict, dataclass, field
from typing import Iterable

OPTIONAL_MODULES = {
    "mcp": "MCP server optional dependency",
    "fastembed": "local embedding provider",
    "neo4j": "Neo4j graph backend",
    "psycopg2": "Postgres driver",
    "asyncpg": "Postgres async driver",
    "redis": "Redis backend",
    "docling": "document parsing integration",
    "playwright": "scraping integration",
    "tavily": "scraping integration",
    "baml_py": "structured-output integration",
}

CONFIG_IMPORTS = [
    ("cognee", "package"),
    ("cognee.infrastructure.llm.config", "LLMConfig"),
    ("cognee.infrastructure.databases.vector.embeddings.config", "EmbeddingConfig"),
    ("cognee.infrastructure.databases.graph.config", "GraphConfig"),
    ("cognee.infrastructure.databases.vector.config", "VectorConfig"),
    ("cognee.infrastructure.databases.relational.config", "RelationalConfig"),
]


@dataclass
class ImportStatus:
    name: str
    available: bool
    detail: str = ""


@dataclass
class Summary:
    package: str = "cognee"
    package_importable: bool = False
    package_version: str | None = None
    config_objects: list[ImportStatus] = field(default_factory=list)
    optional_modules: list[ImportStatus] = field(default_factory=list)


def check_import(module: str, symbol: str | None = None) -> ImportStatus:
    try:
        imported = __import__(module, fromlist=[symbol] if symbol else [])
        if symbol:
            getattr(imported, symbol)
        return ImportStatus(name=symbol or module, available=True)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return ImportStatus(name=symbol or module, available=False, detail=str(exc))


def build_summary() -> Summary:
    summary = Summary()
    pkg_status = check_import("cognee")
    summary.package_importable = pkg_status.available
    if pkg_status.available:
        import cognee

        summary.package_version = getattr(cognee, "__version__", None)

    for module, symbol in CONFIG_IMPORTS[1:]:
        summary.config_objects.append(check_import(module, symbol))

    for module, detail in OPTIONAL_MODULES.items():
        status = check_import(module)
        status.detail = detail if status.available else status.detail
        summary.optional_modules.append(status)

    return summary


def render_text(summary: Summary) -> str:
    lines = [f"Cognee package importable: {summary.package_importable}"]
    lines.append(f"Cognee version: {summary.package_version or 'unknown'}")
    lines.append("Config objects:")
    for item in summary.config_objects:
        suffix = "ok" if item.available else f"missing ({item.detail})"
        lines.append(f"- {item.name}: {suffix}")
    lines.append("Optional modules:")
    for item in summary.optional_modules:
        suffix = "present" if item.available else f"missing ({item.detail})"
        lines.append(f"- {item.name}: {suffix}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a Cognee installation safely.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    args = parser.parse_args()

    summary = build_summary()
    if args.json:
        print(json.dumps(asdict(summary), indent=2, sort_keys=True))
    else:
        print(render_text(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
