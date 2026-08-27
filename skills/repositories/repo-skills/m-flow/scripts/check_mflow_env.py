#!/usr/bin/env python3
"""Safe M-flow environment diagnostic.

This helper checks whether an installed M-flow runtime is importable, which
public entry points/config variables are visible, and which optional service
signals appear configured. It does not add data, run memorization, connect to
external databases, start services, or print local filesystem paths.

Examples:
    python scripts/check_mflow_env.py
    python scripts/check_mflow_env.py --json
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import shutil
import sys
from typing import Any

SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD")
CORE_EXPORTS = [
    "add",
    "memorize",
    "learn",
    "search",
    "query",
    "ingest",
    "datasets",
    "delete",
    "update",
    "prune",
    "config",
    "run_custom_pipeline",
]
ENV_GROUPS = {
    "llm": ["LLM_API_KEY", "LLM_PROVIDER", "LLM_MODEL", "LLM_ENDPOINT", "LLM_INSTRUCTOR_MODE"],
    "embedding": ["EMBEDDING_PROVIDER", "EMBEDDING_MODEL", "EMBEDDING_ENDPOINT", "EMBEDDING_API_KEY"],
    "storage": ["DB_PROVIDER", "VECTOR_DB_PROVIDER", "GRAPH_DATABASE_PROVIDER", "DATA_ROOT_DIRECTORY", "SYSTEM_ROOT_DIRECTORY"],
    "auth": ["REQUIRE_AUTHENTICATION", "ENABLE_BACKEND_ACCESS_CONTROL", "FASTAPI_USERS_JWT_SECRET"],
    "service": ["UI_APP_URL", "MFLOW_CLOUD_API_URL", "FACE_API_KEY"],
}


def _mask(name: str, value: str | None) -> str | None:
    if value is None:
        return None
    if any(marker in name.upper() for marker in SECRET_MARKERS):
        if not value:
            return ""
        return "<set>"
    if len(value) > 120:
        return value[:117] + "..."
    return value


def _distribution_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def inspect_runtime() -> dict[str, Any]:
    result: dict[str, Any] = {
        "python": {
            "version": sys.version.split()[0],
            "executableVisible": bool(sys.executable),
        },
        "distributions": {
            "mflow-ai": _distribution_version("mflow-ai"),
            "m_flow": _distribution_version("m_flow"),
        },
        "imports": {},
        "entryPoints": [],
        "cli": {"mflowOnPath": shutil.which("mflow") is not None},
        "environment": {},
        "warnings": [],
    }

    try:
        m_flow = importlib.import_module("m_flow")
        result["imports"]["m_flow"] = {
            "ok": True,
            "version": getattr(m_flow, "__version__", None),
            "exports": {name: hasattr(m_flow, name) for name in CORE_EXPORTS},
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["imports"]["m_flow"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    for group, names in ENV_GROUPS.items():
        result["environment"][group] = {name: _mask(name, os.getenv(name)) for name in names if os.getenv(name) is not None}

    try:
        eps = metadata.entry_points(group="console_scripts")
        result["entryPoints"] = [f"{ep.name}={ep.value}" for ep in eps if ep.name == "mflow"]
    except Exception as exc:  # pragma: no cover - metadata edge case
        result["warnings"].append(f"entry point inspection failed: {type(exc).__name__}: {exc}")

    # Optional imports: report availability without requiring or importing heavy service clients.
    optional_modules = {
        "neo4j": "Neo4j graph backend extra",
        "psycopg2": "Postgres/pgvector extra",
        "chromadb": "ChromaDB vector backend extra",
        "redis": "Redis cache extra",
        "pymilvus": "Milvus vector backend extra",
        "pinecone": "Pinecone vector backend extra",
        "playwright": "browser scraping extra",
        "protego": "crawler robots.txt parser extra",
        "modal": "distributed workers extra",
        "mcp": "MCP server package dependency",
    }
    result["optionalImports"] = {
        module: {"available": importlib.util.find_spec(module) is not None, "purpose": purpose}
        for module, purpose in optional_modules.items()
    }

    return result


def print_text(report: dict[str, Any]) -> None:
    print("M-flow environment diagnostic")
    print(f"Python: {report['python']['version']}")
    print("Distributions:")
    for name, version in report["distributions"].items():
        print(f"  - {name}: {version or 'not found'}")
    imp = report["imports"].get("m_flow", {})
    print(f"m_flow import: {'ok' if imp.get('ok') else 'failed'}")
    if imp.get("ok"):
        print(f"m_flow.__version__: {imp.get('version')}")
        missing = [name for name, ok in imp.get("exports", {}).items() if not ok]
        print(f"public exports: {'all expected present' if not missing else 'missing ' + ', '.join(missing)}")
    else:
        print(f"import error: {imp.get('error')}")
    print(f"mflow CLI on PATH: {report['cli']['mflowOnPath']}")
    print("console entry points:")
    for ep in report["entryPoints"] or ["<none>"]:
        print(f"  - {ep}")
    print("configured environment groups:")
    for group, values in report["environment"].items():
        print(f"  - {group}: {', '.join(sorted(values)) if values else '<none visible>'}")
    unavailable = [name for name, info in report.get("optionalImports", {}).items() if not info["available"]]
    if unavailable:
        print("optional imports not installed:", ", ".join(sorted(unavailable)))
    for warning in report.get("warnings", []):
        print("warning:", warning)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check installed M-flow runtime without running live workflows.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    report = inspect_runtime()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    mflow_ok = report["imports"].get("m_flow", {}).get("ok", False)
    return 0 if mflow_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
