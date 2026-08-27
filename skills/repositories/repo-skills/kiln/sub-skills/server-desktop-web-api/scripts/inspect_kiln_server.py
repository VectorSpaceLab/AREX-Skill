#!/usr/bin/env python3
"""Inspect Kiln FastAPI route/tag metadata without starting uvicorn."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import a Kiln FastAPI app and report route/tag coverage without "
            "starting uvicorn or calling provider services. Run inside an "
            "environment where the Kiln packages or checkout are importable."
        )
    )
    parser.add_argument(
        "--app",
        choices=("server", "desktop"),
        default="desktop",
        help="App to inspect: core kiln_server app or desktop studio app. Default: desktop.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print route count and tag counts. Enabled by default unless --json-only is used.",
    )
    parser.add_argument(
        "--list-routes",
        action="store_true",
        help="Print method/path/name/tags for each HTTP route.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also print a JSON payload with app, routes, tag_counts, and untagged_api_routes.",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Print only JSON. Implies --json and suppresses human-readable output.",
    )
    parser.add_argument(
        "--repo-root",
        help=(
            "Optional Kiln checkout root to add to sys.path before importing the "
            "desktop studio app. Use this when --app desktop is selected from an "
            "installed package environment."
        ),
    )
    return parser


def _load_app(app_kind: str, repo_root: str | None = None) -> Any:
    os.environ.setdefault("KILN_SKIP_REMOTE_MODEL_LIST", "true")
    if repo_root:
        sys.path.insert(0, os.path.abspath(repo_root))
    if app_kind == "server":
        module = importlib.import_module("kiln_server.server")
    else:
        module = importlib.import_module("app.desktop.desktop_server")
    return module.make_app()


def _methods(route: Any) -> list[str]:
    methods = getattr(route, "methods", None)
    if not methods:
        return []
    return sorted(str(m) for m in methods if str(m) not in {"HEAD", "OPTIONS"})


def _iter_http_routes(app: Any) -> Iterable[dict[str, Any]]:
    for route in getattr(app, "routes", []):
        methods = _methods(route)
        if not methods:
            continue
        path = getattr(route, "path", "")
        endpoint = getattr(route, "endpoint", None)
        name = getattr(route, "name", None) or getattr(endpoint, "__name__", "")
        tags = list(getattr(route, "tags", []) or [])
        yield {
            "methods": methods,
            "path": path,
            "name": name,
            "tags": tags,
            "include_in_schema": bool(getattr(route, "include_in_schema", True)),
        }


def _tag_counts(routes: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for route in routes:
        for tag in route["tags"]:
            counter[tag] += 1
    return dict(sorted(counter.items()))


def _untagged_api_routes(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        route
        for route in routes
        if route["include_in_schema"]
        and (route["path"].startswith("/api/") or route["path"] == "/ping")
        and not route["tags"]
    ]


def _paths_by_tag(routes: list[dict[str, Any]]) -> dict[str, list[str]]:
    by_tag: dict[str, list[str]] = defaultdict(list)
    for route in routes:
        label = f"{','.join(route['methods'])} {route['path']}"
        for tag in route["tags"] or ["<untagged>"]:
            by_tag[tag].append(label)
    return {tag: paths for tag, paths in sorted(by_tag.items())}


def _print_summary(payload: dict[str, Any]) -> None:
    print(f"app: {payload['app']}")
    print(f"http_route_count: {payload['route_count']}")
    if payload["tag_counts"]:
        print("tags:")
        for tag, count in payload["tag_counts"].items():
            print(f"  {tag}: {count}")
    if payload["untagged_api_routes"]:
        print("untagged_api_routes:")
        for route in payload["untagged_api_routes"]:
            print(f"  {','.join(route['methods'])} {route['path']} {route['name']}")


def _print_routes(routes: list[dict[str, Any]]) -> None:
    print("routes:")
    for route in routes:
        tags = ",".join(route["tags"]) if route["tags"] else "-"
        print(
            f"  {','.join(route['methods']):8s} {route['path']:75s} "
            f"{route['name']:35s} {tags}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.json_only:
        args.json = True

    try:
        app = _load_app(args.app, args.repo_root)
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"Failed to import Kiln {args.app} app: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        print(
            "Run this inside a Kiln checkout, pass --repo-root PATH for the "
            "desktop app, or use --app server when only kiln-server is installed.",
            file=sys.stderr,
        )
        return 2

    routes = list(_iter_http_routes(app))
    payload = {
        "app": args.app,
        "route_count": len(routes),
        "tag_counts": _tag_counts(routes),
        "untagged_api_routes": _untagged_api_routes(routes),
        "paths_by_tag": _paths_by_tag(routes),
        "routes": routes,
    }

    if not args.json_only:
        if args.summary or not args.list_routes:
            _print_summary(payload)
        if args.list_routes:
            _print_routes(routes)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if payload["untagged_api_routes"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
