#!/usr/bin/env python3
"""Inspect the bundled DeepSearcher FastAPI helper without starting a server."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve().parent / "serve_deepsearcher_api.py"
_SPEC = importlib.util.spec_from_file_location("deepsearcher_cli_and_service_serve", SCRIPT_PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - import-time safeguard
    raise RuntimeError(f"Could not load bundled service helper from {SCRIPT_PATH}")
serve_deepsearcher_api = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = serve_deepsearcher_api
_SPEC.loader.exec_module(serve_deepsearcher_api)

EXPECTED_ROUTES = {
    "POST /set-provider-config/",
    "POST /load-files/",
    "POST /load-website/",
    "GET /query/",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the bundled DeepSearcher service routes.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser.parse_args()


def collect_routes(app) -> list[str]:
    routes: list[str] = []
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if not path or not methods:
            continue
        for method in sorted(m for m in methods if m not in {"HEAD", "OPTIONS"}):
            routes.append(f"{method} {path}")
    return routes


def main() -> int:
    args = parse_args()
    app = serve_deepsearcher_api.app
    routes = collect_routes(app)
    route_set = set(routes)
    missing = sorted(EXPECTED_ROUTES - route_set)
    ok = not missing
    report: dict[str, Any] = {
        "ok": ok,
        "route_count": len(app.routes),
        "runtime_route_count": len(routes),
        "routes": routes,
        "expected_routes": sorted(EXPECTED_ROUTES),
        "missing_routes": missing,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("DeepSearcher service route check")
        print("===============================")
        print(f"route_count: {report['route_count']}")
        print(f"runtime_route_count: {report['runtime_route_count']}")
        print(f"expected_routes: {', '.join(report['expected_routes'])}")
        if missing:
            print(f"missing_routes: {', '.join(missing)}")
        else:
            print("missing_routes: none")
        for route in routes:
            print(f"- {route}")
        print(f"overall: {'PASS' if ok else 'FAIL'}")

    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
