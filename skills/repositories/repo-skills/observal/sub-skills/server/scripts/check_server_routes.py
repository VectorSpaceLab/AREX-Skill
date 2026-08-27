#!/usr/bin/env python3
"""Import Observal's server route registry and print router metadata as JSON.

This helper only imports the `routes` module. It does not call create_app(),
FastAPI lifespan startup, database migrations, Redis, or ClickHouse setup.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback as tb
from collections import Counter
from pathlib import Path
from typing import Any


def _resolve_server_path(raw: str) -> Path:
    candidate = Path(raw).expanduser()
    if not candidate.exists():
        raise FileNotFoundError(f"server path does not exist: {raw}")
    candidate = candidate.resolve()
    if candidate.is_file():
        candidate = candidate.parent
    if (candidate / "routes.py").is_file():
        return candidate
    nested = candidate / "observal-server"
    if (nested / "routes.py").is_file():
        return nested
    raise FileNotFoundError(
        f"could not find routes.py under {candidate}; pass --server-path pointing at observal-server or repo root"
    )


def _prepend_import_paths(server_path: Path) -> None:
    candidates = [server_path]
    repo_root = server_path.parent
    candidates.append(repo_root)
    shared = repo_root / "packages" / "observal-shared"
    if shared.is_dir():
        candidates.append(shared)

    for path in reversed(candidates):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def _json_default(value: Any) -> str:
    return str(value)


def _router_record(router: Any, index: int) -> dict[str, Any]:
    prefix = getattr(router, "prefix", "")
    tags = list(getattr(router, "tags", []) or [])
    routes = list(getattr(router, "routes", []) or [])
    methods: Counter[str] = Counter()
    route_paths: list[str] = []
    for route in routes:
        path = getattr(route, "path", None)
        if isinstance(path, str):
            route_paths.append(path)
        for method in getattr(route, "methods", []) or []:
            methods[str(method)] += 1
    return {
        "index": index,
        "prefix": prefix,
        "tags": tags,
        "route_count": len(routes),
        "methods": dict(sorted(methods.items())),
        "sample_paths": route_paths[:8],
    }


def _load_routes(server_path: Path) -> dict[str, Any]:
    _prepend_import_paths(server_path)
    routes_mod = importlib.import_module("routes")
    rest_routers = list(getattr(routes_mod, "REST_ROUTERS"))
    routers = [_router_record(router, index) for index, router in enumerate(rest_routers)]
    prefixes = [record["prefix"] for record in routers]
    duplicate_prefixes = sorted(prefix for prefix, count in Counter(prefixes).items() if count > 1)
    return {
        "ok": True,
        "server_path": str(server_path),
        "routes_module": str(Path(getattr(routes_mod, "__file__", "")).resolve()),
        "rest_router_count": len(rest_routers),
        "prefixes": prefixes,
        "unique_prefixes": sorted(set(prefixes)),
        "duplicate_prefixes": duplicate_prefixes,
        "graphql_prefix": "/api/v1/graphql" if hasattr(routes_mod, "include_graphql_routes") else None,
        "routers": routers,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--server-path",
        default=".",
        help="Path to observal-server or to the repository root containing observal-server (default: current directory).",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--traceback", action="store_true", help="Include traceback lines on import failure.")
    args = parser.parse_args(argv)

    try:
        server_path = _resolve_server_path(args.server_path)
        payload = _load_routes(server_path)
        status = 0
    except Exception as exc:  # noqa: BLE001 - CLI helper should report any import/setup failure as JSON.
        payload = {
            "ok": False,
            "server_path": args.server_path,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "hint": (
                "Activate/install the Observal server environment and pass --server-path to observal-server "
                "or the repo root. This helper imports routes but does not run app startup."
            ),
        }
        if args.traceback:
            payload["traceback"] = tb.format_exc().splitlines()
        status = 1

    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True, default=_json_default))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
