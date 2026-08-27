#!/usr/bin/env python3
"""Inspect DocsGPT API route declarations without importing the app.

This script is intentionally AST-based so it can run before Postgres, Redis,
Celery, or the ASGI app are available. It scans application/api for Flask and
Flask-RESTX route decorators plus explicit add_url_rule registrations.
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

HTTP_METHOD_NAMES = {"get", "post", "put", "patch", "delete", "head", "options"}


@dataclass(order=True)
class RouteRecord:
    """One statically discovered route declaration."""

    full_path: str
    methods: list[str]
    object_name: str
    decorator_owner: str
    file: str
    raw_path: str
    kind: str


def _literal(node: ast.AST | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _route_owner(call: ast.Call) -> str | None:
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    if func.attr not in {"route", "add_url_rule"}:
        return None
    owner = func.value
    if isinstance(owner, ast.Name):
        return owner.id
    if isinstance(owner, ast.Attribute):
        return owner.attr
    return None


def _join_paths(prefix: str, route: str) -> str:
    if not prefix or prefix == "/":
        return route if route.startswith("/") else f"/{route}"
    if route == "/":
        return f"/{prefix.strip('/')}"
    return f"/{prefix.strip('/')}/{route.strip('/')}"


def _decorator_methods(call: ast.Call) -> list[str] | None:
    for kw in call.keywords:
        if kw.arg == "methods":
            methods = _literal(kw.value)
            if isinstance(methods, (list, tuple)):
                return sorted(str(m).upper() for m in methods)
    return None


def _class_methods(cls: ast.ClassDef) -> list[str]:
    methods = sorted(
        item.name.upper()
        for item in cls.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name.lower() in HTTP_METHOD_NAMES
    )
    return methods or ["GET"]


def _prefix_maps(tree: ast.Module) -> dict[str, str]:
    prefixes: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if not names:
            continue
        call = node.value
        kind = _call_name(call.func)
        if kind not in {"Namespace", "Blueprint"}:
            continue
        prefix = ""
        for kw in call.keywords:
            if kind == "Namespace" and kw.arg == "path":
                prefix = _literal(kw.value) or ""
            if kind == "Blueprint" and kw.arg == "url_prefix":
                prefix = _literal(kw.value) or ""
        for name in names:
            prefixes[name] = prefix
    return prefixes


def _route_record(
    *,
    repo: Path,
    path: Path,
    owner: str,
    raw_path: str,
    methods: list[str],
    object_name: str,
    kind: str,
    prefixes: dict[str, str],
) -> RouteRecord:
    full_path = _join_paths(prefixes.get(owner, ""), raw_path)
    return RouteRecord(
        full_path=full_path,
        methods=methods,
        object_name=object_name,
        decorator_owner=owner,
        file=str(path.relative_to(repo)),
        raw_path=raw_path,
        kind=kind,
    )


def scan_routes(repo: Path) -> list[RouteRecord]:
    api_dir = repo / "application" / "api"
    records: list[RouteRecord] = []
    seen: set[tuple[str, str, str, str]] = set()

    for path in sorted(api_dir.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            raise SystemExit(f"Could not parse {path}: {exc}") from exc

        prefixes = _prefix_maps(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # Decorator-based routes.
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                owner = _route_owner(decorator)
                if not owner or not decorator.args:
                    continue
                raw_path = _literal(decorator.args[0])
                if not isinstance(raw_path, str):
                    raw_path = ast.unparse(decorator.args[0])
                methods = _decorator_methods(decorator)
                if methods is None:
                    methods = _class_methods(node) if isinstance(node, ast.ClassDef) else ["GET"]
                record = _route_record(
                    repo=repo,
                    path=path,
                    owner=owner,
                    raw_path=raw_path,
                    methods=methods,
                    object_name=node.name,
                    kind="decorator",
                    prefixes=prefixes,
                )
                key = (record.full_path, ",".join(record.methods), record.object_name, record.kind)
                if key not in seen:
                    seen.add(key)
                    records.append(record)

            # Explicit add_url_rule registrations.
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for inner in ast.walk(node):
                    if not isinstance(inner, ast.Call):
                        continue
                    if not isinstance(inner.func, ast.Attribute) or inner.func.attr != "add_url_rule":
                        continue
                    if not inner.args:
                        continue
                    owner = _route_owner(inner)
                    if not owner:
                        continue
                    raw_path = _literal(inner.args[0])
                    if not isinstance(raw_path, str):
                        raw_path = ast.unparse(inner.args[0])
                    methods = _decorator_methods(inner) or ["GET"]
                    record = _route_record(
                        repo=repo,
                        path=path,
                        owner=owner,
                        raw_path=raw_path,
                        methods=methods,
                        object_name=node.name,
                        kind="add_url_rule",
                        prefixes=prefixes,
                    )
                    key = (record.full_path, ",".join(record.methods), record.object_name, record.kind)
                    if key not in seen:
                        seen.add(key)
                        records.append(record)

    return sorted(records)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect DocsGPT route declarations without app startup")
    parser.add_argument("--repo", default=".", help="DocsGPT repository root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text table")
    parser.add_argument("--contains", help="Only show routes containing this substring")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / "application" / "api").is_dir():
        raise SystemExit(f"{repo} does not look like a DocsGPT checkout: missing application/api")

    records = scan_routes(repo)
    if args.contains:
        records = [record for record in records if args.contains in record.full_path]

    if args.json:
        print(json.dumps([asdict(record) for record in records], indent=2, sort_keys=True))
        return 0

    for record in records:
        print(
            f"{','.join(record.methods):18} {record.full_path:55} "
            f"{record.object_name:32} {record.kind:12} {record.file}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
