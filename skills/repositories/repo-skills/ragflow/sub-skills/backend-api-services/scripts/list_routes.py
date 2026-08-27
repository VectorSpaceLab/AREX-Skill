#!/usr/bin/env python3
"""Statically list RAGFlow-style @manager.route declarations.

This helper parses Python source without importing the application, so it is safe
for offline route audits. It performs no network calls, starts no services, and
modifies no files.
"""
from __future__ import annotations

import argparse
import ast
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Route:
    file: str
    line: int
    function: str
    blueprint: str
    rule: str
    methods: tuple[str, ...]
    inferred_prefix: str

    @property
    def full_path(self) -> str:
        if not self.inferred_prefix:
            return self.rule
        return self.inferred_prefix.rstrip("/") + "/" + self.rule.lstrip("/")


def literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def literal_methods(node: ast.AST | None) -> tuple[str, ...]:
    if node is None:
        return ("GET",)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [literal_string(item) for item in node.elts]
        return tuple(value.upper() for value in values if value) or ("GET",)
    value = literal_string(node)
    return (value.upper(),) if value else ("<dynamic>",)


def route_from_decorator(decorator: ast.AST) -> tuple[str, str, tuple[str, ...]] | None:
    if not isinstance(decorator, ast.Call):
        return None
    func = decorator.func
    if not isinstance(func, ast.Attribute) or func.attr != "route":
        return None
    if not isinstance(func.value, ast.Name):
        return None
    if not decorator.args:
        return None
    rule = literal_string(decorator.args[0])
    if rule is None:
        rule = "<dynamic>"
    methods_node = None
    for keyword in decorator.keywords:
        if keyword.arg == "methods":
            methods_node = keyword.value
            break
    return func.value.id, rule, literal_methods(methods_node)


def infer_prefix(path: Path, root: Path) -> str:
    parts = path.relative_to(root).parts if path.is_relative_to(root) else path.parts
    normalized = "/".join(parts)
    full_normalized = path.as_posix()
    context = f"/{normalized} /{full_normalized}"
    if "/restful_apis/" in context or normalized.startswith("restful_apis/"):
        return "/api/v1"
    if path.name == "backward_compat.py":
        return "<backward_compat: /api/v1 or /v1>"
    if path.name.endswith("_app.py"):
        page_name = path.stem.removesuffix("_app")
        return f"/v1/{page_name}"
    if "/sdk/" in context or normalized.startswith("sdk/"):
        return f"/v1/{path.stem}"
    return ""


def iter_python_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix == ".py":
            yield root
        return
    for path in sorted(root.rglob("*.py")):
        if any(part in {".git", "__pycache__", ".venv", "venv", "node_modules"} for part in path.parts):
            continue
        yield path


def parse_file(path: Path, root: Path) -> list[Route]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        print(f"warning: skipped {path}: {exc}", file=sys.stderr)
        return []

    routes: list[Route] = []
    display_file = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    prefix = infer_prefix(path, root)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            parsed = route_from_decorator(decorator)
            if parsed is None:
                continue
            blueprint, rule, methods = parsed
            routes.append(
                Route(
                    file=display_file,
                    line=node.lineno,
                    function=node.name,
                    blueprint=blueprint,
                    rule=rule,
                    methods=methods,
                    inferred_prefix=prefix,
                )
            )
    return routes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statically list @manager.route declarations from a RAGFlow API source tree or copied snippets."
    )
    parser.add_argument(
        "--root",
        default=".",
        type=Path,
        help="Directory or Python file to scan. Defaults to the current directory.",
    )
    parser.add_argument(
        "--format",
        choices=("table", "csv"),
        default="table",
        help="Output format. Defaults to table.",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Only include inferred/full paths containing this substring.",
    )
    parser.add_argument(
        "--method",
        default="",
        help="Only include routes with this HTTP method, such as GET or POST.",
    )
    return parser


def filter_routes(routes: list[Route], prefix: str, method: str) -> list[Route]:
    method = method.upper().strip()
    result = []
    for route in routes:
        if prefix and prefix not in route.full_path and prefix not in route.inferred_prefix:
            continue
        if method and method not in route.methods:
            continue
        result.append(route)
    return result


def print_table(routes: list[Route]) -> None:
    headers = ("METHODS", "FULL_PATH", "FUNCTION", "FILE:LINE")
    rows = [
        (
            ",".join(route.methods),
            route.full_path,
            route.function,
            f"{route.file}:{route.line}",
        )
        for route in routes
    ]
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]
    print("  ".join(header.ljust(width) for header, width in zip(headers, widths)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)))


def print_csv(routes: list[Route]) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(["methods", "full_path", "rule", "inferred_prefix", "blueprint", "function", "file", "line"])
    for route in routes:
        writer.writerow([
            ",".join(route.methods),
            route.full_path,
            route.rule,
            route.inferred_prefix,
            route.blueprint,
            route.function,
            route.file,
            route.line,
        ])


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if not root.exists():
        print(f"error: root does not exist: {root}", file=sys.stderr)
        return 2

    routes: list[Route] = []
    scan_root = root if root.is_dir() else root.parent
    for path in iter_python_files(root):
        routes.extend(parse_file(path, scan_root))
    routes = filter_routes(sorted(routes, key=lambda item: (item.full_path, item.file, item.line)), args.prefix, args.method)

    if args.format == "csv":
        print_csv(routes)
    else:
        print_table(routes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
