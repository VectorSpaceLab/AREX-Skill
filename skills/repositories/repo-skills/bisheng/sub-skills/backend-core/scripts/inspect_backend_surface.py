#!/usr/bin/env python3
"""Inspect BiSheng backend core files without importing the application.

Example:
  python inspect_backend_surface.py --repo-root .

The helper reports routers, domain-like modules, SQLModel model files, error-code
files, and focused pytest directories. It is safe to run without databases or
other BiSheng services.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


def parse_router_includes(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    includes: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "include_router" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Name):
                    includes.append(arg.id)
                else:
                    includes.append(ast.unparse(arg) if hasattr(ast, "unparse") else "<expr>")
    return includes


def class_names(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def list_dirs(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(child.name for child in path.iterdir() if child.is_dir() and not child.name.startswith("."))


def list_files(path: Path, pattern: str = "*.py") -> list[str]:
    if not path.exists():
        return []
    return sorted(child.name for child in path.glob(pattern) if child.is_file())


def inspect(repo: Path) -> dict[str, Any]:
    backend = repo / "src/backend"
    bisheng = backend / "bisheng"
    tests = backend / "test"
    modules = []
    for child in bisheng.iterdir() if bisheng.exists() else []:
        if child.is_dir() and not child.name.startswith("__"):
            shape = {
                "name": child.name,
                "has_api": (child / "api").is_dir(),
                "has_domain": (child / "domain").is_dir(),
                "has_router": (child / "api/router.py").exists(),
            }
            if shape["has_api"] or shape["has_domain"]:
                modules.append(shape)
    return {
        "router_includes_v1_v2": parse_router_includes(bisheng / "api/router.py"),
        "app_factory_classes": class_names(bisheng / "main.py"),
        "domain_modules": modules,
        "database_model_files": list_files(bisheng / "database/models"),
        "error_code_files": list_files(bisheng / "common/errcode"),
        "common_schema_classes": class_names(bisheng / "common/schemas/api.py"),
        "settings_classes": class_names(bisheng / "core/config/settings.py"),
        "test_directories": list_dirs(tests),
        "key_files_present": {
            "main.py": (bisheng / "main.py").exists(),
            "api/router.py": (bisheng / "api/router.py").exists(),
            "common/schemas/api.py": (bisheng / "common/schemas/api.py").exists(),
            "core/config/settings.py": (bisheng / "core/config/settings.py").exists(),
            "pyproject.toml": (backend / "pyproject.toml").exists(),
        },
    }


def print_text(data: dict[str, Any]) -> None:
    print("BiSheng backend core surface")
    print("============================")
    print("key files:")
    for key, value in data["key_files_present"].items():
        print(f"  {key:28} {'OK' if value else 'MISSING'}")
    print("\nrouter includes:")
    for item in data["router_includes_v1_v2"]:
        print(f"  - {item}")
    print("\ndomain/api modules:")
    for item in data["domain_modules"]:
        flags = ", ".join(k for k in ("has_api", "has_domain", "has_router") if item[k])
        print(f"  - {item['name']} ({flags})")
    print("\nmodel files:", len(data["database_model_files"]))
    print("test directories:", ", ".join(data["test_directories"][:80]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect BiSheng backend core surface.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    data = inspect(Path(args.repo_root).resolve())
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_text(data)
    return 0 if all(data["key_files_present"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
