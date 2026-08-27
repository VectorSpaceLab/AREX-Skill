#!/usr/bin/env python3
"""Statically list FastAPI routes defined in Nexent backend app modules.

The scanner parses Python AST only. It never imports repository modules, starts
FastAPI, opens network connections, or evaluates arbitrary code. It is safe to
run from any working directory when --repo-root points at a Nexent checkout.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


@dataclass(frozen=True)
class RouterInfo:
    name: str
    prefix: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RouteInfo:
    method: str
    path: str
    module: str
    endpoint: str
    router: str
    router_prefix: str
    route_path: str
    lineno: int
    tags: list[str]
    services: list[str]
    databases: list[str]
    exceptions: list[str]
    auth_helpers: list[str]


@dataclass(frozen=True)
class ModuleInfo:
    module: str
    path: str
    routers: list[RouterInfo]
    routes: list[RouteInfo]
    services: list[str]
    databases: list[str]
    exceptions: list[str]
    auth_helpers: list[str]
    include_routers: list[str]
    app_factories: list[str]
    warnings: list[str]


def _ast_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - ast.unparse exists on supported Python.
        return node.__class__.__name__


def _literal_or_source(node: ast.AST | None, default: Any = None) -> Any:
    if node is None:
        return default
    try:
        return ast.literal_eval(node)
    except Exception:
        return _ast_unparse(node)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return []


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return _ast_unparse(func)


def _decorator_receiver(func: ast.AST) -> str:
    if isinstance(func, ast.Attribute):
        return _ast_unparse(func.value)
    return ""


def _join_paths(prefix: str, route_path: str) -> str:
    prefix = (prefix or "").strip()
    route_path = (route_path or "").strip()
    if not prefix and not route_path:
        return "/"
    if route_path and not route_path.startswith("/"):
        route_path = "/" + route_path
    if not prefix:
        return route_path or "/"
    if route_path in {"", "/"}:
        return prefix.rstrip("/") or "/"
    return f"{prefix.rstrip('/')}/{route_path.lstrip('/')}".replace("//", "/")


def _relative_module(apps_dir: Path, file_path: Path) -> str:
    rel = file_path.relative_to(apps_dir.parent).with_suffix("")
    return ".".join(rel.parts)


def _find_repo_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "backend" / "apps").is_dir():
            return candidate
    return None


def resolve_repo_root(raw: str | None) -> Path:
    if raw:
        root = Path(raw).expanduser().resolve()
    else:
        root = _find_repo_root(Path.cwd().resolve())
        if root is None:
            raise SystemExit("Could not find backend/apps from cwd; pass --repo-root.")
    apps_dir = root / "backend" / "apps"
    if not apps_dir.is_dir():
        raise SystemExit(f"Not a Nexent repo root: missing {apps_dir}")
    return root


def _imported_symbols(tree: ast.Module) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {
        "services": [],
        "databases": [],
        "exceptions": [],
        "auth_helpers": [],
    }
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        module = node.module or ""
        names = [alias.name for alias in node.names]
        if module.startswith("services"):
            result["services"].append(module)
        if module.startswith("database") or module.startswith("nexent.vector_database"):
            result["databases"].append(module)
        if module == "consts.exceptions":
            result["exceptions"].extend(names)
        if module == "utils.auth_utils" or module.endswith("permission_utils"):
            result["auth_helpers"].extend(names)
    for key, values in result.items():
        result[key] = sorted(dict.fromkeys(values))
    return result


def _router_assignments(tree: ast.Module) -> dict[str, RouterInfo]:
    routers: dict[str, RouterInfo] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if _call_name(node.value) != "APIRouter":
            continue
        prefix = ""
        tags: list[str] = []
        for keyword in node.value.keywords:
            if keyword.arg == "prefix":
                prefix = str(_literal_or_source(keyword.value, ""))
            elif keyword.arg == "tags":
                tags = _string_list(_literal_or_source(keyword.value, []))
        for target in node.targets:
            if isinstance(target, ast.Name):
                routers[target.id] = RouterInfo(name=target.id, prefix=prefix, tags=tags)
    return routers


def _decorator_route(dec: ast.AST) -> tuple[str, str, str] | None:
    if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
        return None
    method = dec.func.attr.lower()
    if method not in HTTP_METHODS:
        return None
    receiver = _decorator_receiver(dec.func)
    route_path = ""
    if dec.args:
        route_path = str(_literal_or_source(dec.args[0], ""))
    return method.upper(), receiver, route_path


def _route_tags(dec: ast.Call, router_tags: list[str]) -> list[str]:
    tags = list(router_tags)
    for keyword in dec.keywords:
        if keyword.arg == "tags":
            tags.extend(_string_list(_literal_or_source(keyword.value, [])))
    return sorted(dict.fromkeys(tags))


def _include_router_calls(tree: ast.Module) -> list[str]:
    calls: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "include_router":
            continue
        if node.args:
            calls.append(_ast_unparse(node.args[0]))
    return sorted(dict.fromkeys(calls))


def _app_factory_calls(tree: ast.Module) -> list[str]:
    calls: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name not in {"create_app", "FastAPI"}:
            continue
        fields: list[str] = [name]
        for keyword in node.keywords:
            if keyword.arg in {"title", "description", "version", "root_path"}:
                value = _literal_or_source(keyword.value, None)
                fields.append(f"{keyword.arg}={value!r}")
        calls.append("(" + ", ".join(fields) + ")")
    return calls


def parse_app_module(apps_dir: Path, file_path: Path) -> ModuleInfo:
    module_name = _relative_module(apps_dir, file_path)
    warnings: list[str] = []
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        return ModuleInfo(
            module=module_name,
            path=str(file_path.relative_to(apps_dir.parent.parent)),
            routers=[],
            routes=[],
            services=[],
            databases=[],
            exceptions=[],
            auth_helpers=[],
            include_routers=[],
            app_factories=[],
            warnings=[f"syntax error: {exc}"],
        )

    imports = _imported_symbols(tree)
    routers = _router_assignments(tree)
    routes: list[RouteInfo] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            parsed = _decorator_route(dec)
            if parsed is None:
                continue
            method, router_name, route_path = parsed
            router = routers.get(router_name, RouterInfo(name=router_name))
            tags = _route_tags(dec, router.tags) if isinstance(dec, ast.Call) else router.tags
            routes.append(
                RouteInfo(
                    method=method,
                    path=_join_paths(router.prefix, route_path),
                    module=module_name,
                    endpoint=node.name,
                    router=router.name,
                    router_prefix=router.prefix,
                    route_path=route_path,
                    lineno=getattr(node, "lineno", 0),
                    tags=tags,
                    services=imports["services"],
                    databases=imports["databases"],
                    exceptions=imports["exceptions"],
                    auth_helpers=imports["auth_helpers"],
                )
            )

    routes.sort(key=lambda item: (item.path, item.method, item.module, item.endpoint, item.lineno))
    return ModuleInfo(
        module=module_name,
        path=str(file_path.relative_to(apps_dir.parent.parent)),
        routers=sorted(routers.values(), key=lambda item: item.name),
        routes=routes,
        services=imports["services"],
        databases=imports["databases"],
        exceptions=imports["exceptions"],
        auth_helpers=imports["auth_helpers"],
        include_routers=_include_router_calls(tree),
        app_factories=_app_factory_calls(tree),
        warnings=warnings,
    )


def scan_routes(repo_root: Path) -> list[ModuleInfo]:
    apps_dir = repo_root / "backend" / "apps"
    modules = [parse_app_module(apps_dir, path) for path in sorted(apps_dir.glob("*.py"))]
    return modules


def _short(values: Iterable[str], limit: int = 2) -> str:
    unique = list(dict.fromkeys(values))
    if not unique:
        return "-"
    shown = unique[:limit]
    extra = len(unique) - len(shown)
    text = ", ".join(shown)
    return f"{text} (+{extra})" if extra else text


def print_table(modules: list[ModuleInfo]) -> None:
    routes = [route for module in modules for route in module.routes]
    print(f"FastAPI routes discovered: {len(routes)}")
    print("Method  Path                                                    Module endpoint                         Services")
    print("------  ------------------------------------------------------  --------------------------------------  ------------------------------")
    for route in sorted(routes, key=lambda item: (item.path, item.method, item.module, item.endpoint)):
        owner = f"{route.module}.{route.endpoint}"
        print(f"{route.method:<6}  {route.path:<54.54}  {owner:<38.38}  {_short(route.services)}")

    duplicates: dict[tuple[str, str], list[RouteInfo]] = {}
    for route in routes:
        duplicates.setdefault((route.method, route.path), []).append(route)
    duplicate_items = {key: val for key, val in duplicates.items() if len(val) > 1}
    if duplicate_items:
        print("\nPotential duplicate method/path pairs:")
        for (method, path), items in sorted(duplicate_items.items()):
            owners = ", ".join(f"{item.module}.{item.endpoint}" for item in items)
            print(f"  {method} {path}: {owners}")

    include_only = [module for module in modules if module.include_routers and not module.routes]
    if include_only:
        print("\nApp composition modules:")
        for module in include_only:
            print(f"  {module.module}: includes {', '.join(module.include_routers)}")

    warnings = [warning for module in modules for warning in module.warnings]
    if warnings:
        print("\nWarnings:", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)


def to_jsonable(modules: list[ModuleInfo], repo_root: Path) -> dict[str, Any]:
    routes = [route for module in modules for route in module.routes]
    duplicates = []
    by_key: dict[tuple[str, str], list[RouteInfo]] = {}
    for route in routes:
        by_key.setdefault((route.method, route.path), []).append(route)
    for (method, path), items in sorted(by_key.items()):
        if len(items) > 1:
            duplicates.append(
                {
                    "method": method,
                    "path": path,
                    "owners": [f"{item.module}.{item.endpoint}" for item in items],
                }
            )
    return {
        "schema_version": 1,
        "repo_root_name": repo_root.name,
        "route_count": len(routes),
        "module_count": len(modules),
        "duplicates": duplicates,
        "modules": [asdict(module) for module in modules],
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statically list FastAPI routes in Nexent backend/apps without importing backend code.",
    )
    parser.add_argument(
        "--repo-root",
        help="Path to the Nexent repository root. If omitted, search upward from the current directory.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text table.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    repo_root = resolve_repo_root(args.repo_root)
    modules = scan_routes(repo_root)
    if args.json:
        print(json.dumps(to_jsonable(modules, repo_root), indent=2, sort_keys=True))
    else:
        print_table(modules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
