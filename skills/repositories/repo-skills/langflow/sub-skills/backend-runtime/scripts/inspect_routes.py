#!/usr/bin/env python3
"""Inspect FastAPI/Starlette routes from an importable module.

Examples:
    python inspect_routes.py --module langflow.api.router --router router
    python inspect_routes.py --module my_package.main --router app --include-hidden
"""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RouteInfo:
    methods: str
    path: str
    name: str
    include_in_schema: bool | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a module containing a FastAPI, Starlette, or APIRouter object and print its routes.",
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Dotted module path to import, for example 'langflow.api.router' or 'my_app.main'.",
    )
    parser.add_argument(
        "--router",
        default="router",
        help="Attribute name containing a FastAPI app, Starlette app, or APIRouter. Default: router.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include routes whose include_in_schema flag is false.",
    )
    parser.add_argument(
        "--path-prefix",
        default="",
        help="Only show routes whose path starts with this prefix, such as '/api/v1'.",
    )
    parser.add_argument(
        "--method",
        action="append",
        default=[],
        help="Filter by HTTP method. May be passed multiple times, for example --method GET --method POST.",
    )
    return parser.parse_args()


def import_router(module_name: str, router_attr: str) -> Any:
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise SystemExit(
            f"Could not import module '{module_name}'. Install Langflow or the target package in the active "
            f"Python environment, then retry. Original error: {exc}"
        ) from exc

    try:
        return getattr(module, router_attr)
    except AttributeError as exc:
        available = ", ".join(sorted(name for name in dir(module) if not name.startswith("_"))[:25])
        raise SystemExit(
            f"Module '{module_name}' does not define attribute '{router_attr}'. "
            f"Available public attributes include: {available or '(none)'}"
        ) from exc


def iter_raw_routes(router: Any) -> Iterable[Any]:
    routes = getattr(router, "routes", None)
    if routes is None:
        raise SystemExit(
            "The selected object does not expose a '.routes' attribute. Pass --router with a FastAPI, "
            "Starlette, or APIRouter object."
        )
    return routes


def route_methods(route: Any) -> list[str]:
    methods = getattr(route, "methods", None)
    if not methods:
        return []
    return sorted(method for method in methods if method not in {"HEAD", "OPTIONS"})


def collect_routes(router: Any, *, include_hidden: bool, path_prefix: str, methods: set[str]) -> list[RouteInfo]:
    collected: list[RouteInfo] = []
    for route in iter_raw_routes(router):
        path = getattr(route, "path", None)
        if not isinstance(path, str):
            continue
        include_in_schema = getattr(route, "include_in_schema", None)
        if include_in_schema is False and not include_hidden:
            continue
        if path_prefix and not path.startswith(path_prefix):
            continue

        route_method_list = route_methods(route)
        if methods and not methods.intersection(route_method_list):
            continue

        collected.append(
            RouteInfo(
                methods=",".join(route_method_list) if route_method_list else "-",
                path=path,
                name=str(getattr(route, "name", "")),
                include_in_schema=include_in_schema,
            )
        )
    return sorted(collected, key=lambda item: (item.path, item.methods, item.name))


def print_routes(routes: list[RouteInfo]) -> None:
    if not routes:
        print("No matching routes found.")
        return

    method_width = max(len("METHODS"), *(len(route.methods) for route in routes))
    schema_width = len("SCHEMA")
    print(f"{'METHODS':<{method_width}}  {'PATH':<60}  {'NAME':<35}  {'SCHEMA':<{schema_width}}")
    print(f"{'-' * method_width}  {'-' * 60}  {'-' * 35}  {'-' * schema_width}")
    for route in routes:
        schema = "yes" if route.include_in_schema is not False else "no"
        print(f"{route.methods:<{method_width}}  {route.path:<60}  {route.name:<35}  {schema:<{schema_width}}")


def main() -> int:
    args = parse_args()
    methods = {method.upper() for method in args.method}
    router = import_router(args.module, args.router)
    routes = collect_routes(
        router,
        include_hidden=args.include_hidden,
        path_prefix=args.path_prefix,
        methods=methods,
    )
    print_routes(routes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
