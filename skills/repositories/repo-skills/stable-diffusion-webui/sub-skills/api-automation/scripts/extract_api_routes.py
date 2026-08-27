#!/usr/bin/env python3
"""Extract Stable Diffusion WebUI FastAPI route registrations without importing WebUI."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


class RouteExtractor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.routes: list[dict[str, Any]] = []

    def visit_Call(self, node: ast.Call) -> None:
        if self._is_add_api_route(node.func) and node.args:
            path = self._literal_or_source(node.args[0])
            if not isinstance(path, str) or not path.startswith("/"):
                self.generic_visit(node)
                return
            endpoint = self._endpoint_name(node.args[1]) if len(node.args) > 1 else None
            route: dict[str, Any] = {
                "path": path,
                "endpoint": endpoint,
                "methods": self._methods(node),
                "response_model": self._response_model(node),
                "conditional": self._conditional_context(node),
                "line": node.lineno,
            }
            self.routes.append(route)
        self.generic_visit(node)

    @staticmethod
    def _is_add_api_route(func: ast.AST) -> bool:
        return isinstance(func, ast.Attribute) and func.attr == "add_api_route"

    @staticmethod
    def _literal_or_source(node: ast.AST) -> Any:
        try:
            return ast.literal_eval(node)
        except Exception:
            return ast.unparse(node) if hasattr(ast, "unparse") else None

    @staticmethod
    def _endpoint_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Attribute):
            return ast.unparse(node) if hasattr(ast, "unparse") else node.attr
        if isinstance(node, ast.Name):
            return node.id
        return ast.unparse(node) if hasattr(ast, "unparse") else None

    @classmethod
    def _methods(cls, node: ast.Call) -> list[str]:
        for keyword in node.keywords:
            if keyword.arg == "methods":
                value = cls._literal_or_source(keyword.value)
                if isinstance(value, list):
                    return [str(item) for item in value]
                if isinstance(value, tuple):
                    return [str(item) for item in value]
                if isinstance(value, str):
                    return [value]
        return []

    @classmethod
    def _response_model(cls, node: ast.Call) -> str | None:
        for keyword in node.keywords:
            if keyword.arg == "response_model":
                return ast.unparse(keyword.value) if hasattr(ast, "unparse") else cls._literal_or_source(keyword.value)
        return None

    @staticmethod
    def _conditional_context(node: ast.AST) -> str | None:
        parent = getattr(node, "_parent", None)
        while parent is not None:
            if isinstance(parent, ast.If):
                return ast.unparse(parent.test) if hasattr(ast, "unparse") else "conditional"
            parent = getattr(parent, "_parent", None)
        return None


def attach_parents(tree: ast.AST) -> None:
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            setattr(child, "_parent", parent)


def extract_routes(source: Path) -> list[dict[str, Any]]:
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    attach_parents(tree)
    extractor = RouteExtractor()
    extractor.visit(tree)
    return extractor.routes


def render_markdown(routes: list[dict[str, Any]]) -> str:
    lines = ["| Path | Methods | Endpoint | Response model | Conditional | Line |", "| --- | --- | --- | --- | --- | --- |"]
    for route in routes:
        methods = ", ".join(route.get("methods") or [])
        lines.append(
            "| {path} | {methods} | {endpoint} | {response_model} | {conditional} | {line} |".format(
                path=route.get("path") or "",
                methods=methods,
                endpoint=route.get("endpoint") or "",
                response_model=route.get("response_model") or "",
                conditional=route.get("conditional") or "",
                line=route.get("line") or "",
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract add_api_route registrations from modules/api/api.py")
    parser.add_argument("--source", required=True, help="Path to modules/api/api.py or a compatible source file")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format")
    args = parser.parse_args()

    routes = extract_routes(Path(args.source))
    if args.format == "json":
        print(json.dumps(routes, indent=2, sort_keys=True))
    else:
        print(render_markdown(routes), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
