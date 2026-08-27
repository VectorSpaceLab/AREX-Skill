#!/usr/bin/env python3
"""Read-only Honcho runtime check.

The script summarizes configuration, route coverage, and optional embedding
validation. It is safe to run repeatedly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "src").exists():
            return candidate
    return start


def _ensure_repo_on_path() -> Path:
    root = _find_repo_root(Path(__file__).resolve())
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def _config_summary() -> dict[str, Any]:
    from src.config import settings

    return {
        "DB": {
            "CONNECTION_URI": settings.DB.CONNECTION_URI,
            "SCHEMA": settings.DB.SCHEMA,
            "POOL_CLASS": settings.DB.POOL_CLASS,
            "CONNECT_TIMEOUT_SECONDS": settings.DB.CONNECT_TIMEOUT_SECONDS,
        },
        "EMBEDDING": {
            "VECTOR_DIMENSIONS": settings.EMBEDDING.VECTOR_DIMENSIONS,
            "MAX_INPUT_TOKENS": settings.EMBEDDING.MAX_INPUT_TOKENS,
        },
        "VECTOR_STORE": {
            "TYPE": settings.VECTOR_STORE.TYPE,
            "MIGRATED": settings.VECTOR_STORE.MIGRATED,
            "NAMESPACE": settings.VECTOR_STORE.NAMESPACE,
        },
        "SUMMARY": {
            "ENABLED": settings.SUMMARY.ENABLED,
            "MESSAGES_PER_SHORT_SUMMARY": settings.SUMMARY.MESSAGES_PER_SHORT_SUMMARY,
            "MESSAGES_PER_LONG_SUMMARY": settings.SUMMARY.MESSAGES_PER_LONG_SUMMARY,
        },
        "LLM": {
            "DEFAULT_MAX_TOKENS": settings.LLM.DEFAULT_MAX_TOKENS,
        },
    }


def _route_summary() -> list[dict[str, Any]]:
    from src.main import app

    routes: list[dict[str, Any]] = []
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if not path or not methods:
            continue
        if path in {"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}:
            continue
        routes.append({"path": path, "methods": sorted(methods)})
    return routes


async def _check_embedding_schema() -> str:
    from src.db import engine
    from src.startup import validate_embedding_schema

    await validate_embedding_schema(engine)
    return "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument(
        "--check-db",
        action="store_true",
        help="Run the embedding-schema validator if the project imports cleanly",
    )
    args = parser.parse_args()

    root = _ensure_repo_on_path()
    report: dict[str, Any] = {"project_root": str(root)}

    try:
        report["config"] = _config_summary()
        report["routes"] = _route_summary()
        report["route_count"] = len(report["routes"])
        report["imports"] = {"src.main": "ok", "src.config": "ok"}
    except Exception as exc:  # pragma: no cover - inspection helper
        report["error"] = str(exc)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"Honcho runtime check failed: {exc}")
        return 1

    if args.check_db:
        try:
            import asyncio

            report["embedding_validation"] = asyncio.run(_check_embedding_schema())
        except Exception as exc:  # pragma: no cover - inspection helper
            report["embedding_validation_error"] = str(exc)
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print(f"Embedding validation failed: {exc}")
            return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Honcho runtime check")
        print(f"Project root: {report['project_root']}")
        print(f"Routes: {report['route_count']}")
        print("Embedding dimensions:", report["config"]["EMBEDDING"]["VECTOR_DIMENSIONS"])
        print("Vector store type:", report["config"]["VECTOR_STORE"]["TYPE"])
        if args.check_db:
            print("Embedding validation: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
