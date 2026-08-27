#!/usr/bin/env python3
"""List top-level classes and functions without importing the target module.

This is a structured, portable replacement for grep-style class/function
inventory helpers. It parses Python source with ast, so it avoids config,
provider, and optional-dependency side effects from importing MetaGPT modules.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Iterable, Iterator


PYTHON_FILE_SUFFIX = ".py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List classes and functions from Python files using AST parsing.")
    parser.add_argument(
        "path",
        nargs="?",
        help="Python file or package directory to inspect. Omit when using --module.",
    )
    parser.add_argument(
        "--module",
        help="Dotted module or package name to resolve from the current Python path without importing it.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a readable table.")
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum directory depth below the target package root. 0 means only files directly in the target.",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="Include names starting with an underscore and dunder methods/classes.",
    )
    parser.add_argument(
        "--include-methods",
        action="store_true",
        help="Include class methods in each class record.",
    )
    parser.add_argument(
        "--sort",
        choices=("path", "name"),
        default="path",
        help="Sort records by source path/line or symbol name.",
    )
    return parser.parse_args()


def resolve_target(path_arg: str | None, module: str | None) -> Path:
    if bool(path_arg) == bool(module):
        raise SystemExit("Provide exactly one target: a path argument or --module.")

    if path_arg:
        target = Path(path_arg).expanduser().resolve()
        if not target.exists():
            raise SystemExit(f"Target path does not exist: {path_arg}")
        return target

    assert module is not None
    parts = module.split(".")
    candidates: list[Path] = []
    search_roots = [Path.cwd(), *(Path(entry or ".") for entry in sys.path)]
    for root_candidate in search_roots:
        root = root_candidate.resolve()
        module_path = root.joinpath(*parts)
        if module_path.is_dir():
            candidates.append(module_path)
        py_path = module_path.with_suffix(PYTHON_FILE_SUFFIX)
        if py_path.is_file():
            candidates.append(py_path)

    if not candidates:
        raise SystemExit(f"Could not resolve module without importing it: {module}")

    return candidates[0]


def iter_python_files(target: Path, max_depth: int | None) -> Iterator[Path]:
    if target.is_file():
        if target.suffix == PYTHON_FILE_SUFFIX:
            yield target
        return

    root = target.resolve()
    for path in root.rglob(f"*{PYTHON_FILE_SUFFIX}"):
        if any(part in {"__pycache__", ".git", ".tox", ".nox"} for part in path.parts):
            continue
        if max_depth is not None:
            relative_parent = path.parent.relative_to(root)
            depth = 0 if str(relative_parent) == "." else len(relative_parent.parts)
            if depth > max_depth:
                continue
        yield path


def is_public(name: str, include_private: bool) -> bool:
    return include_private or not name.startswith("_")


def format_args(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    args: list[str] = []
    all_args = [*node.args.posonlyargs, *node.args.args]
    for arg in all_args:
        args.append(arg.arg)
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    for arg in node.args.kwonlyargs:
        args.append(arg.arg)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    return args


def base_names(node: ast.ClassDef) -> list[str]:
    names: list[str] = []
    for base in node.bases:
        try:
            names.append(ast.unparse(base))
        except Exception:
            names.append(type(base).__name__)
    return names


def parse_file(path: Path, root: Path, include_private: bool, include_methods: bool) -> list[dict]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [
            {
                "kind": "error",
                "name": "SyntaxError",
                "path": safe_relative(path, root),
                "line": exc.lineno or 0,
                "message": exc.msg,
            }
        ]
    except UnicodeDecodeError as exc:
        return [
            {
                "kind": "error",
                "name": "UnicodeDecodeError",
                "path": safe_relative(path, root),
                "line": 0,
                "message": str(exc),
            }
        ]

    records: list[dict] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and is_public(node.name, include_private):
            record = {
                "kind": "class",
                "name": node.name,
                "path": safe_relative(path, root),
                "line": node.lineno,
                "bases": base_names(node),
            }
            if include_methods:
                methods = []
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(
                        child.name, include_private
                    ):
                        methods.append(
                            {
                                "name": child.name,
                                "line": child.lineno,
                                "async": isinstance(child, ast.AsyncFunctionDef),
                                "args": format_args(child),
                            }
                        )
                record["methods"] = methods
            records.append(record)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(node.name, include_private):
            records.append(
                {
                    "kind": "function",
                    "name": node.name,
                    "path": safe_relative(path, root),
                    "line": node.lineno,
                    "async": isinstance(node, ast.AsyncFunctionDef),
                    "args": format_args(node),
                }
            )
    return records


def safe_relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def collect_symbols(
    target: Path,
    max_depth: int | None,
    include_private: bool,
    include_methods: bool,
) -> list[dict]:
    root = target if target.is_dir() else target.parent
    records: list[dict] = []
    for path in iter_python_files(target, max_depth):
        records.extend(parse_file(path, root, include_private, include_methods))
    return records


def sort_records(records: Iterable[dict], mode: str) -> list[dict]:
    if mode == "name":
        return sorted(records, key=lambda item: (item.get("name", ""), item.get("path", ""), item.get("line", 0)))
    return sorted(records, key=lambda item: (item.get("path", ""), item.get("line", 0), item.get("name", "")))


def print_table(records: list[dict]) -> None:
    if not records:
        return
    width = max(len(record.get("path", "")) for record in records)
    for record in records:
        path = record.get("path", "")
        line = record.get("line", 0)
        kind = record.get("kind", "")
        name = record.get("name", "")
        suffix = ""
        if kind == "function":
            async_prefix = "async " if record.get("async") else ""
            suffix = f" {async_prefix}({', '.join(record.get('args', []))})"
        elif kind == "class" and record.get("bases"):
            suffix = f" bases={','.join(record['bases'])}"
        elif kind == "error":
            suffix = f" {record.get('message', '')}"
        print(f"{path:<{width}}:{line:<4} {kind:<8} {name}{suffix}")
        for method in record.get("methods", []):
            async_prefix = "async " if method.get("async") else ""
            print(f"{path:<{width}}:{method['line']:<4} method   {name}.{method['name']} {async_prefix}({', '.join(method.get('args', []))})")


def main() -> int:
    args = parse_args()
    target = resolve_target(args.path, args.module)
    records = collect_symbols(
        target=target,
        max_depth=args.max_depth,
        include_private=args.include_private,
        include_methods=args.include_methods,
    )
    records = sort_records(records, args.sort)
    if args.json:
        print(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        print_table(records)
    return 1 if any(record.get("kind") == "error" for record in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
